from mesa import Agent
from . import utility


class Agent(Agent):
    """an (expected) utility maximizing agent,
    capable of managing long-term goals"""

    def __init__(self, state, goals):
        self.state = state
        self.goals = goals

    def actions(self, state, world):
        """the agent's possible actions
        for a given agent state and world state"""
        raise NotImplementedError

    def successors(self, state, world):
        """the agent's possible successors (expected states)
        for a given agent state and world state"""
        actions = self.actions(state, world)

        # compute expected states
        succs = []
        for action in actions:
            expstate = utility.expected_state(state, action.outcomes)

            # TODO make this better/abstract out
            expected_world = world.copy()
            expected_world['time'] += action.cost
            succs.append((action, (expstate, expected_world)))

        # sort by expected utility, desc
        succs = sorted(succs, key=lambda s: utility.utility(state, s[1][0]), reverse=True)
        return succs

    def subplan(self, state, world, goal):
        """create a subplan to achieve a goal;
        i.e. the prerequisites for an action"""
        pass

    def _subplan_succ_func(self, state):
        """successor function compatible with the subplanning algorithm"""
        for action, (child, world) in self.successors(state, {'time': 0}):
            yield action, child

    def _graph_succ_func(self, node):
        """successor function compatible with the expand graph func"""
        act, (state, world) = node
        return self.successors(state, world)

    def utility(self, state):
        """computes utility for a state, in the context of the agent's goals
        and for the state itself"""
        return utility.utility(self.state, state) + sum(utility.utility_for_goal(state, g) for g in self.goals)

    def score_path(self, path):
        """good paths get agents closer to high-priority goals
        have a good average expected utility across all states"""
        _, (final_state, __) = path[-1] # final state
        mean_exp_utility = sum([utility.utility(self.state, s) for a, (s, w) in path])/len(path)
        final_state_utility = utility.utility(self.state, final_state) + sum(utility.utility_for_goal(final_state, g) for g in self.goals)
        return mean_exp_utility * final_state_utility
