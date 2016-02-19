import asyncio
from uuid import uuid4
from agent import utility
from .prereq import Prereq
from .action import Action, Goal
from .search import Planner, hill_climbing
from .state import attenuate_state, attenuate_value
from functools import partial


class Agent():
    """an (expected) utility maximizing agent,
    capable of managing long-term goals"""

    def __init__(self, state, actions, goals, utility_funcs, constraints=None, debug=True):
        self.id = uuid4().hex
        self.goals = set(goals)
        self.actions = actions
        self.ufuncs = utility_funcs
        self.utility = partial(utility.utility, self.ufuncs)
        self.planner = Planner(self._succ_func, self.utility)
        self.constraints = constraints or {}
        self.state = state
        self.debug = debug

    def actions_for_state(self, state):
        """the agent's possible actions
        for a given agent state -
        you probably want to override this"""
        for action in self.actions:
            yield action

    def successors(self, state, goals):
        """the agent's possible successors (expected states)
        for a given agent state"""
        # compute expected states
        succs = []
        for action in self.actions_for_state(state):
            expstate = self._expected_state(action, state)
            succs.append((action, (expstate, goals)))

        for goal in goals:
            if goal.satisfied(state):
                expstate = self._expected_state(goal, state)
                remaining_goals = goals.copy()
                remaining_goals.remove(goal)
                succs.append((goal, (expstate, remaining_goals)))

        # sort by expected utility, desc
        succs = sorted(succs,
                       key=lambda s: self._score_successor(state, s[1][0]),
                       reverse=True)
        return succs

    def _score_successor(self, from_state, to_state):
        """score a successor based how it changes from the previous state"""
        return utility.change_utility(self.ufuncs, from_state, to_state)\
            + utility.goals_utility(self.ufuncs, to_state, self.goals)

    def subplan(self, state, goal):
        """create a subplan to achieve a goal;
        i.e. the prerequisites for an action"""
        return self.planner.ida(self, state, goal.as_action())

    def _succ_func(self, node):
        """for planning; returns successors"""
        act, (state, goals) = node
        return self.successors(state, goals)

    def _valid_func(self, node, pnode):
        """for planning; checks if an action is possible"""
        act, (_, _) = node
        _, (state, _) = pnode
        return act.satisfied(state)

    def plan(self, state, goals, depth=None):
        """generate a plan; uses hill climbing search to minimize searching time.
        will generate new goals for actions which are impossible given the current state but desired"""
        plan, goals = hill_climbing((None, (state, self.goals)), self._succ_func, self._valid_func, depth)
        self.goals = self.goals | goals
        return plan, self.goals

    def _expected_state(self, action, state):
        """computes expected state for an action/goal,
        attenuating it if necessary"""
        state = action.expected_state(state)
        return attenuate_state(state, self.constraints)

    def __setitem__(self, key, val):
        """set a state value, attenuating if necessary"""
        if key in self.constraints:
            val = attenuate_value(val, self.constraints[key])
        self._state[key] = val

    @asyncio.coroutine
    def __getitem__(self, key):
        """retrieves a state value;
        a coroutine for remote access"""
        return self._state[key]

    @property
    def state(self):
        """return a copy of the state"""
        return self._state.copy()

    @state.setter
    def state(self, state):
        """set the entire state at once,
        attenuating as necessary"""
        self._state = attenuate_state(state, self.constraints)

    @asyncio.coroutine
    def call(self, fname, *args, **kwargs):
        """call a method on the agent.
        if another agent needs access to a method, use this method,
        since it supports remote access"""
        return getattr(self, fname)(*args, **kwargs)

    @asyncio.coroutine
    def request(self, propname):
        """get a property from the agent.
        if another agent needs access to a property, use this method,
        sicne it supports remote access"""
        if isinstance(propname, list):
            return [getattr(self, p) for p in propname]
        else:
            return getattr(self, propname)


class AgentProxy():
    worker = None

    """an agent proxy represents an agent that is accessed remotely"""
    def __init__(self, agent):
        self.id = agent.id

    @asyncio.coroutine
    def __getitem__(self, key):
        return (yield from self.worker.query_agent({
            'id': self.id,
            'key': key
        }))

    @asyncio.coroutine
    def call(self, fname, *args, **kwargs):
        return (yield from self.worker.call_agent({
            'id': self.id,
            'func': fname,
            'args': args,
            'kwargs': kwargs
        }))

    @asyncio.coroutine
    def request(self, propname):
        return (yield from self.worker.call_agent({
            'id': self.id,
            'func': 'request',
            'args': (propname,)
        }))

    def __repr__(self):
        return 'AgentProxy({})'.format(self.id)
