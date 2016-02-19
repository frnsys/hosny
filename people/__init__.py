import os
import config
import random
import logging
import asyncio
import numpy as np
from util import ewms
from scipy import stats
from agent import Agent, Goal
from agent.action import PrereqsUnsatisfied
from collections import defaultdict
from world import work
from .names import generate_name
from .generate import generate


# precompute and cache to save a lot of time
emp_dist = work.precompute_employment_dist()


class Person(Agent):
    @classmethod
    def generate(cls, year, given=None, **kwargs):
        """generate a random person"""
        attribs = generate(year, given)
        attribs.pop('year', None)
        attribs.update(kwargs)
        return cls(**attribs)

    """an individual in the city"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.name = generate_name(self.sex, self.race)
        self.dead = False
        self.action_cooldown = 0

        # days to "burn in" agent, so mean utility and stuff settle
        self.burn_in = 14

        self.last_utility = None
        self.mean_utility = None
        self.stddev_utility = 0

        # the world initializes this
        self.friends = []

        # keep track of past day's actions
        self.diary = []

        # keep track of "life" history
        self.history = {
            'salient_actions': [],
            'accomplished_goals': [],
            'failed_actions': defaultdict(int),
            'succeeded_actions': defaultdict(int)
        }

        super().__init__(
            state={
                'health': 1.,
                'stress': 0.5,
                'fatigue': 0.,
                'cash': 0,
                'employed': self.employed,
                'income': self.income,
                'rent_fail': 0,
                'sex': self.sex,
                'race': self.race,
                'education': self.education
            },
            actions=config.ACTIONS,
            goals=[],
            utility_funcs=config.UTILITY_FUNCS,
            constraints=config.CONSTRAINTS)

    def __repr__(self):
        return self.name

    def _is_significant(self, utility, mean, stddev):
        """determines if a utility is significant or not"""
        if utility >= mean + 2.5 * stddev:
            return True
        elif utility <= mean - 2.5 * stddev:
            return True
        return False

    @asyncio.coroutine
    def step(self, world):
        """one time-step"""
        if self.dead:
            return

        if world['time'] == config.START_HOUR:
            # keep track of person's utility at "end" (of the previous) day
            self.last_utility = self.utility(self.state)
            if self.mean_utility is None:
                self.mean_utility = self.last_utility
            else:
                self.mean_utility, self.stddev_utility = ewms(self.mean_utility, self.stddev_utility, self.last_utility)

            if self.burn_in == 0:
                # get salient actions for yesterday
                self.history['salient_actions'].extend([(a, u) for a, s, u in self.diary
                                                        if self._is_significant(
                                                            u, self.mean_utility, self.stddev_utility)])
            else:
                self.burn_in -= 1

            # reset diary for new day
            self.diary = []

            # new day, see what happens
            self.daily_effects(world)

            # update last utility after day's effects
            self.last_utility = self.utility(self.state)

            # update friends
            emp_friends = 0
            for f in self.friends:
                emp = yield from f['employed']
                if emp > 0:
                    emp_friends += 1
            self['employed_friends'] = emp_friends

            # make a plan for day
            yield from self.check_friends()
            self.dayplan, goals = self.plan_day(world)
            self.logger.info('--->plan for the day: {}'.format([action for action, _ in self.dayplan]))

        # if an action is still "executing",
        # skip this step
        if self.action_cooldown > 0:
            self.action_cooldown -= 1

        else:
            action_taken = False
            while not action_taken:
                # try to take next queued action
                try:
                    action, expected_state = self.dayplan.pop(0)
                except IndexError:
                    # if no more of the day is planned, replan from this point
                    self.logger.info('ran out of things to do, replanning')
                    self.dayplan, _ = self.plan_day(world)
                    continue
                try:
                    time_taken = self.take_action(action, world)
                    self.action_cooldown = time_taken
                    action_taken = True
                    self.logger.info('{} did {}'.format(self.name, action))

                    if isinstance(action, Goal):
                        self.history['accomplished_goals'].append(action)

                    # record (action, resulting state, utility)
                    self.last_utility = self.utility(self.state)
                    self.diary.append((action.name, self.state.copy(), self.last_utility))
                    self.history['succeeded_actions'][action] += 1

                except PrereqsUnsatisfied:
                    # replan
                    self.history['failed_actions'][action] += 1

                    self.logger.info('  {} FAILED, REPLANNING'.format(action))
                    self.dayplan, _ = self.plan_day(world)

    def salient_lifetime_actions(self):
        utilities = [u for a, u in self.history['salient_actions']]
        if utilities:
            mean, std = np.mean(utilities), np.std(utilities)
            self.history['salient_actions'] = [(a, u) for a, u in self.history['salient_actions'] if self._is_significant(u, mean, std)]
            return self.history['salient_actions']
        return []

    def actions_for_state(self, state):
        time = state['world.time']
        for action in self.actions:
            # actions limited by time in day
            # assume all actions have some time cost that is constant across all outcomes
            # so we only need to grab the first outcome
            time_cost = action.updates[0].get('world.time', 0)
            if time + time_cost <= config.START_HOUR + config.HOURS_IN_DAY:
                yield action

    def plan_day(self, world):
        """make a plan of what actions to (attempt to) execute through the day,
        starting with the given world state. the agent considers all possible paths through the remaining
        hours of the day, choosing the path that gets them closest to their important goals
        and maximizes average expected utility throughout the day"""
        state = self._joint_state(self.state, world)
        plan = self.plan(state, self.goals)
        return plan

    def take_action(self, action, world):
        """execute an action, applying its effects"""
        state = self._joint_state(self.state, world)
        self.state = action(state)
        self.state, new_world = self._disjoint_state(state)
        time_taken = new_world['time'] - world['time']
        return time_taken

    def _joint_state(self, state, world):
        """create a state combining the agent state and the world's state.
        keys for the world's state are prefixed with 'world.'"""
        state = state.copy()
        state.update({'world.{}'.format(k): v for k, v in world.items()})
        return state

    def _disjoint_state(self, state):
        """separates the agent and world states"""
        world, agent = {}, {}
        for k, v in state.items():
            if k.startswith('world.'):
                k = k[len('world.'):]
                world[k] = v
            else:
                agent[k] = v
        return agent, world

    @asyncio.coroutine
    def check_friends(self):
        """see how friends are doing"""
        for friend in self.friends:
            utility, stddev_utility = yield from friend.request(['last_utility', 'stddev_utility'])
            if utility is not None:
                if utility > utility + 1.5*stddev_utility:
                    # friend had a good day
                    self['stress'] = max(0, self['stress'] - 0.005)
                elif utility < utility - 1.5*stddev_utility:
                    # friend had a bad day
                    self['stress'] = min(1, self['stress'] + 0.005)

    def set_logger(self, log_dir):
        """creates a logger. only run this _after_ agents have
        been distributed to workers; this opens a file which can't be pickled"""
        slug = self.name.lower().replace(' ', '_')
        logger = logging.getLogger(slug)

        # configure the logger
        formatter = logging.Formatter('%(name)s - %(message)s')

        # output to file
        fh = logging.FileHandler(os.path.join(log_dir, '{}.log'.format(slug)))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)
        self.logger = logger

    def daily_effects(self, world):
        """apply daily effects to agent"""
        # if an agent ends the day with <= 0 health, they are dead
        if self.state['health'] <= 0:
            self.dead = True
            return

        # getting sick
        if random.random() < config.SICK_PROB:
            self['health'] -= stats.beta.rvs(2, 10)

        if self.state['employed'] > 0:
            # wage change
            if random.random() < 1/365: # arbitrary probability, what should this be?
                change = work.income_change(world['year'], world['year'] + 1, self.sex, self.race, self.income_bracket)
                self['income'] += change # TODO this needs to change their income bracket if appropriate
            else:
                employment_dist = emp_dist[world['year']][world['month']][self.race.name][self.sex.name]
                p_unemployed = employment_dist['unemployed']/365 # kind of arbitrary denominator, what should this be?
                # fired
                if random.random() < p_unemployed:
                    self['employed'] = 0

        # if the agent fails to pay rent/mortgage 3 months in a row,
        # they get evicted/lose their house
        if self.state['rent_fail'] >= 3:
            # what are the effects of this?
            pass # TODO

        # tick goals/check failures
        remaining_goals = set()
        for goal in self.goals:
            if isinstance(goal, Goal):
                goal.tick()
                if goal.time <= 0:
                    self.state = goal.fail(self.state)
                else:
                    remaining_goals.add(goal)
            else:
                remaining_goals.add(goal)
        self.goals = remaining_goals
