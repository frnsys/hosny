import config
import operator
from uuid import uuid4
from agent import Agent
from agent.action import Goal, Outcome, Prereq, PrereqsUnsatisfied
from .names import generate_name
from .generate import generate


class Person(Agent):
    @classmethod
    def generate(cls, year):
        """generate a random person"""
        attribs = generate(year)
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

        # the world initializes this
        self.friends = []

        # keep track of past day's actions
        self.diary = []

        # long-term goals
        # TODO rent goal should renew every month
        goals = [Goal(
            'pay rent',
            prereqs={'cash': Prereq(operator.ge, self.rent)},
            outcomes=[Outcome({'stress': -0.1, 'rent_fail': -1000}, 1.)],
            failures=[Outcome({'stress': 1, 'rent_fail': 1}, 1.)],
            time=2
        )]

        super().__init__(
            state={
                'health': 1.,
                'stress': 0.5,
                'fatigue': 0,
                'cash': 0,
                'employed': 1,
                'income': self.income,
                'rent_fail': 0
            },
            actions=config.ACTIONS,
            goals=goals,
            utility_funcs=config.UTILITY_FUNCS)

    def __repr__(self):
        return self.name

    def step(self, model):
        """one time-step"""
        if self.dead:
            return

        if model.state['time'] == config.START_HOUR:
            # new day, see what happens
            model.affect(self)

            # make a plan for day
            self.check_friends()
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
                action, expected_state = self.dayplan.pop(0)
                try:
                    time_taken = self.take_action(action, model.state)
                    self.action_cooldown = time_taken
                    action_taken = True
                    print('I did', action)
                    self.diary.append(action.name)
                except PrereqsUnsatisfied:
                    # replan
                    print(action, 'FAILED, REPLANNING')
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
            time_cost = action.outcomes[0].effects.get('world.time', 0)
            if time + time_cost <= config.START_HOUR + config.HOURS_IN_DAY:
                yield action

    def plan_day(self, world):
        """make a plan of what actions to (attempt to) execute through the day,
        starting with the given world state. the agent considers all possible paths through the remaining
        hours of the day, choosing the path that gets them closest to their important goals
        and maximizes average expected utility throughout the day"""
        state = self._joint_state(self.state, world)
        plans = self.plan(state, self.goals, depth=None)

        # preferred plan for the day
        return plans[0]

    def take_action(self, action, world):
        """execute an action, applying its effects"""
        state = self._joint_state(self.state, world)
        state = action(state)
        state = self._attenuate_state(state)
        self.state, new_world = self._disjoint_state(state)
        time_taken = new_world['time'] - world['time']
        return time_taken

    def _attenuate_state(self, state):
        for k, v in state.items():
            # limit value to range if specified
            if k in config.RANGES:
                mn, mx = config.RANGES[k]
                if mn is not None: state[k] = max(mn, state[k])
                if mx is not None: state[k] = min(mx, state[k])
        return state

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
            print('my friend', friend.name, 'did', friend.diary[-1])
