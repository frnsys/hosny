import math
import config
import logging
#import operator
from uuid import uuid4
from util import ewms
from agent import Agent, Prereq, Goal
from agent.action import PrereqsUnsatisfied
from .names import generate_name
from .generate import generate


class Person(Agent):
    @classmethod
    def generate(cls, year, given=None):
        """generate a random person"""
        attribs = generate(year, given)
        attribs.pop('year', None)
        return cls(**attribs)

    """an individual in the city"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.id = uuid4().hex
        self.name = generate_name(self.sex, self.race)
        self.dead = False
        self.action_cooldown = 0

        self.mean_utility = None
        self.var_utility = 0

        # the world initializes this
        self.friends = []

        # keep track of past day's actions
        self.diary = []

        # long-term goals
        # TODO rent goal should renew every month
        #goals = [Goal(
            #'pay rent',
            #prereqs={'cash': Prereq(operator.ge, self.rent)},
            #outcomes=[Outcome({'stress': -0.1, 'rent_fail': -1000}, 1.)],
            #failures=[Outcome({'stress': 1, 'rent_fail': 1}, 1.)],
            #time=2
        #)]
        goals = []

        super().__init__(
            state={
                'health': 1.,
                'stress': 0.5,
                'fatigue': 0,
                'cash': 0,
                'employed': self.employed,
                'income': self.income,
                'rent_fail': 0,
                'sex': self.sex,
                'race': self.race,
                'education': self.education
            },
            actions=config.ACTIONS,
            goals=goals,
            utility_funcs=config.UTILITY_FUNCS,
            ranges=config.RANGES,
            dtypes=config.DTYPES)

    def __repr__(self):
        return self.name

    @profile
    def step(self, model):
        """one time-step"""
        if self.dead:
            return

        if model.state['time'] == config.START_HOUR:
            # new day, see what happens
            model.affect(self)

            # keep track of person's utility at "end" (of the previous) day
            self.last_utility = self.utility(self.state)
            if self.mean_utility is None:
                self.mean_utility = self.last_utility
            else:
                self.mean_utility, self.var_utility = ewms(self.mean_utility, self.var_utility, self.last_utility)

            # update friends
            self.state['employed_friends'] = sum(f['employed'] for f in self.friends)

            # make a plan for day
            self.check_friends()
            print('planning day')
            self.dayplan = self.plan_day(model.state)
            print('plan for the day', self.dayplan)


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
                    print('ran out of things to do, replanning')
                    self.dayplan = self.plan_day(model.state)
                    continue
                try:
                    time_taken = self.take_action(action, model.state)
                    self.action_cooldown = time_taken
                    action_taken = True
                    print(self.name, 'did', action)

                    # record (action, success, resulting state)
                    self.diary.append((action.name, True, self.state.copy()))

                except PrereqsUnsatisfied:
                    # replan
                    print('  ', action, 'FAILED, REPLANNING')
                    # record (action, success, failing state)
                    self.diary.append((action.name, False, self.state.copy()))

                    self.dayplan = self.plan_day(model.state)

    def actions_for_state(self, state):
        time = state['world.time']
        for action in self.actions:
            # check that the action is possible from the state
            if not action.satisfied(state):
                continue

            # actions limited by time in day
            # assume all actions have some time cost that is constant across all outcomes
            # so we only need to grab the first outcome
            time_cost = action.outcomes.updates[0].get('world.time', 0)
            if time + time_cost <= config.START_HOUR + config.HOURS_IN_DAY:
                yield action

    def _valid_plan(self, plan):
        """only full-day plans are considered"""
        _, (state, _) = plan[-1]
        return state['world.time'] == 24

    def plan_day(self, world):
        """make a plan of what actions to (attempt to) execute through the day,
        starting with the given world state. the agent considers all possible paths through the remaining
        hours of the day, choosing the path that gets them closest to their important goals
        and maximizes average expected utility throughout the day"""
        state = self._joint_state(self.state, world)
        plan, new_goals = self.plan(state, self.goals, depth=None, predicate=self._valid_plan)
        self.goals = new_goals
        return plan

    @profile
    def take_action(self, action, world):
        """execute an action, applying its effects"""
        state = self._joint_state(self.state, world)
        state = action(state)
        state = self._attenuate_state(state)
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

    def check_friends(self):
        """see how friends are doing"""
        for friend in self.friends:
            if friend.diary:
                action, success, state = friend.diary[-1]
                if friend.utility > friend.utility + 2*math.sqrt(friend.var_utility):
                    print('friend had a good day')
                    self.state['stress'] = max(0, self.state['stress'] - 0.005)
                elif friend.utility < friend.utility - 2*math.sqrt(friend.var_utility):
                    print('friend had a bad day')
                    self.state['stress'] = min(1, self.state['stress'] + 0.005)

    def set_logger(self, log_path):
        """creates a logger"""
        logger = logging.getLogger(self.name)

        # configure the logger
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)s - %(message)s')

        # output to file
        fh = logging.FileHandler(log_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        self.logger = logger
