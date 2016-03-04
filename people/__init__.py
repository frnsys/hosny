import os
import config
import random
import logging
import asyncio
import numpy as np
from util import ewms
from scipy import stats
from cess import Agent, Goal
from world import work
from .names import generate_name
from .generate import generate


# precompute and cache to save a lot of time
emp_dist = work.precompute_employment_dist()


# assuming 1 adult. ofc these expenses will vary a lot depending on other
# factors like neighborhood, but we could not find data that granular
import json
annual_expenses = sum(json.load(open('data/world/annual_expenses.json', 'r'))['1 adult'].values())


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
            'accomplished_goals': []
        }

        # values estimated from
        # Temporal Discounting in Choice Between Delayed Rewards: The Role of Age and Income
        # Leonard Green, Joel Myerson, David Lichtman, Suzanne Rosen, Astrid Fry
        # <http://psych.wustl.edu/lengreen/publications/Temporal%20discounting%20in%20choice%20between%20delayed%20rewards%20(1996).pdf>
        self.discounting_rate = 0.01 if self.wage_income > 50000 else 0.046

        super().__init__(
            state={
                'health': 1.,
                'stress': 0.5,
                'cash': 1000,
                'employed': self.employed,
                'wage_income': self.wage_income,
                'business_income': self.business_income,
                'investment_income': self.investment_income,
                'retirement_income': self.retirement_income,
                'welfare_income': self.welfare_income,
                'rent_fail': 0,
                'sex': self.sex,
                'race': self.race,
                'age': int(self.age),
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

        # keep track of person's utility at "end" (of the previous) day
        self.last_utility = self.utility(self.state)
        if self.mean_utility is None:
            self.mean_utility = self.last_utility
        else:
            self.mean_utility, self.stddev_utility = ewms(self.mean_utility, self.stddev_utility, self.last_utility)

        if self.burn_in == 0:
            # get salient actions for yesterday
            self.history['salient_actions'].extend([(a, u) for a, s, u in self.diary
                                                    if self._is_significant(u, self.mean_utility, self.stddev_utility)])
        else:
            self.burn_in -= 1

        # make money off non-wage income
        for income_attr in ['business_income', 'investment_income', 'retirement_income', 'welfare_income']:
            self.state['cash'] += self.state[income_attr]/365

        # pay (very roughly estimated) expenses
        self.state['cash'] -= annual_expenses/365 * (0.5 + stats.beta.rvs(2,2))

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

        yield from self.check_friends()

        # make a plan for day
        action = self.plan_day(world)

        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('TAKING ACTION', action.name)
        self.take_action(action, world)

        if isinstance(action, Goal):
            self.history['accomplished_goals'].append(action)

        # record (action, resulting state, utility)
        self.last_utility = self.utility(self.state)
        self.diary.append((action.name, self.state.copy(), self.last_utility))
        print('GOALS', self.goals)

    def salient_lifetime_actions(self):
        # utilities = [u for a, u in self.history['salient_actions']]
        # if utilities:
            # mean, std = np.mean(utilities), np.std(utilities)
            # self.history['salient_actions'] = [(a, u) for a, u in self.history['salient_actions'] if self._is_significant(u, mean, std)]
            # return self.history['salient_actions']
        # return []
        return self.id, self.name, self.diary, self.goals

    def plan_day(self, world):
        """agents execute only one action per day
        (to keep the model computationally feasible at large scales).
        they choose the actiont that maximizes expected utility
        and gets them closer to their goals"""
        state = self._joint_state(self.state, world)

        # returns all successors, even ones not possible
        # in this state, so we can consider aspirational actions
        # (which become goals)
        succs = self.successors(state, self.goals)

        for action, _ in succs:
            if not action.satisfied(state):
                self.goals.add(action)
            else:
                return action

    def take_action(self, action, world):
        """execute an action, applying its effects"""
        state = self._joint_state(self.state, world)

        for g in self.goals:
            if g.name == action.name:
                self.goals.remove(g)

        print('BEFORE STATE ------------------')
        print(self.state)
        self.state = action(state)
        print('AFTER STATE ------------------')
        print(self.state)
        print('------------------------------')
        self.state, new_world = self._disjoint_state(state)

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
            self.state['health'] -= stats.beta.rvs(2, 10)

        if self.state['employed'] == 1:
            # wage change
            if random.random() < 1/365: # arbitrary probability, what should this be?
                # change = work.income_change(world['year'], world['year'] + 1, self.sex, self.race, self.wage_income_bracket, 'INCWAGE')
                # self.state['wage_income'] += change # TODO this needs to change their income bracket if appropriate
                pass
            else:
                employment_dist = emp_dist[world['year']][world['month'] - 1][self.race.name][self.sex.name]
                p_unemployed = employment_dist['unemployed']/365 # kind of arbitrary denominator, what should this be?
                # fired
                if random.random() < p_unemployed:
                    self.state['employed'] = 0

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
                    if goal.repeats:
                        goal.reset()
                        remaining_goals.add(goal)
                else:
                    remaining_goals.add(goal)
            else:
                remaining_goals.add(goal)
        self.goals = remaining_goals
