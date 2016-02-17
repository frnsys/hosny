from .search import Planner, hill_climbing
from .action import Action, Goal
from .prereq import Prereq
from .state import attenuate_state, attenuate_value
from agent import utility
from functools import partial


class Agent():
    """an (expected) utility maximizing agent,
    capable of managing long-term goals"""

    def __init__(self, state, actions, goals, utility_funcs, constraints=None, debug=True):
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
        actions = self.actions_for_state(state)

        # compute expected states
        succs = []
        for action in actions:
            expstate = self._expected_state(action, state)
            succs.append((action, (expstate, goals)))

        for goal in goals:
            if goal.satisfied(state):
                expstate = self._expected_state(goal, state)
                remaining_goals = goals.copy()
                remaining_goals.remove(goal)
                succs.append((action, (expstate, remaining_goals)))

        # sort by expected utility, desc
        succs = sorted(succs,
                       key=lambda s: self._score_successor(state, s[1][0]),
                       reverse=True)
        return succs

    def _score_successor(self, from_state, to_state):
        return utility.change_utility(self.ufuncs, from_state, to_state)\
            + utility.goals_utility(self.ufuncs, to_state, self.goals)

    def subplan(self, state, goal):
        """create a subplan to achieve a goal;
        i.e. the prerequisites for an action"""
        return self.planner.ida(self, state, goal.as_action())

    def _succ_func(self, node):
        act, (state, goals) = node
        return self.successors(state, goals)

    def _valid_func(self, node, pnode):
        act, (_, _) = node
        _, (state, _) = pnode
        return act.satisfied(state)

    def plan(self, state, goals, depth=None):
        # TODO pass in a scoring function for hill climbing, e.g.
        # self.score_plan, to take into account closeness to goals
        # TODO go through all actions, including impossible ones
        # if hill climbing wants to choose an action that is not yet possible,
        # set it as a goal, then backtrack and keep going
        plan, goals = hill_climbing((None, (state, self.goals)), self._succ_func, self._valid_func, depth)
        self.goals = self.goals | goals
        return plan, self.goals

    def _expected_state(self, action, state):
        """computes expected state for an action/goal,
        attenuating it if necessary"""
        state = action.expected_state(state)
        return attenuate_state(state, self.constraints)

    def __setitem__(self, key, val):
        if key in self.constraints:
            val = attenuate_value(val, self.constraints[key])
        self._state[key] = val

    def __getitem__(self, key):
        return self._state[key]

    @property
    def state(self):
        return self._state.copy()

    @state.setter
    def state(self, state):
        self._state = attenuate_state(state, self.constraints)
