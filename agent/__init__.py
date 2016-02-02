from mesa import Agent
from .search import Planner, expand_graph
from .utility import Utility
from .action import Action, Goal
from .prereq import Prereq


class Agent(Agent):
    """an (expected) utility maximizing agent,
    capable of managing long-term goals"""

    def __init__(self, state, actions, goals, utility_funcs):
        self.state = state
        self.goals = set(goals)
        self.actions = actions
        self.utility = Utility(utility_funcs)
        self.planner = Planner(self._plan_succ_func, self.utility.utility)

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
            expstate = action.expected_state(state)
            succs.append((action, (expstate, goals)))

        for goal in goals:
            if goal.satisfied(state):
                expstate = goal.expected_state(state)
                remaining_goals = goals.copy()
                remaining_goals.remove(goal)
                succs.append((action, (expstate, remaining_goals)))

        # sort by expected utility, desc
        succs = sorted(succs, key=lambda s: self.utility.utility(state, s[1][0]), reverse=True)
        return succs

    def subplan(self, state, goal):
        """create a subplan to achieve a goal;
        i.e. the prerequisites for an action"""
        return self.planner.ida(self, state, goal.as_action())

    def _graph_succ_func(self, node):
        """successor function compatible with the expand graph func"""
        act, (state, goals) = node
        return self.successors(state, goals)

    def _plan_succ_func(self, state):
        """successor function compatible with the expand graph func"""
        # assume goals=[], that is, ignore other goals for subplanning
        # should we change this?
        for action, node in self.successors(state, []):
            # discard the remaining goals
            state, _ = node
            yield action, state

    def score_path(self, path):
        """good paths get agents closer to high-priority goals
        have a good average expected utility across all states"""
        _, (final_state, _) = path[-1] # final state

        # mean expected utility over all states in the path
        mean_exp_utility = sum([self.utility.utility(self.state, s) for a, (s, g) in path])/len(path)

        final_state_utility = self.utility.utility(self.state, final_state) + \
            sum(self.utility.utility_for_goal(final_state, g) for g in self.goals)
        return mean_exp_utility * final_state_utility

    def make_plans(self, state, goals, depth):
        """generate plans to the specified depth, from the specified starting state,
        sorted by scores (expected utility and closeness to goals)"""
        succs = self.successors(state, goals)

        # generate starting nodes
        plans = [[(action, node)] for action, node in succs]

        # generate the graph
        plans = [path for path in expand_graph(plans, self._graph_succ_func, max_depth=depth)]

        # rank plans by utilities of the expected states
        plans = sorted(plans, key=lambda p: self.score_path(p), reverse=True)
        return plans

    def plan(self, state, goals, depth):
        """selects a fully-satisfied plan
        from all possible plans, adding goals as necessary"""
        plans = self.make_plans(state, goals, depth)
        new_goals = goals.copy()
        while plans:
            satisfied = True
            last_state = state.copy()
            plan = plans.pop(0)
            for action, (s, g) in plan:
                if not action.satisfied(last_state):
                    new_goals.add(action)
                    satisfied = False
                    # this action can't be executed,
                    # so the state will not change -
                    # thus don't update last_state
                else:
                    last_state = s
            if satisfied:
                break
            else:
                # resort plans, since plan values may change
                # now that we have new goals
                plans = sorted(plans, key=lambda p: self.score_path(p), reverse=True)
        return plan, new_goals
