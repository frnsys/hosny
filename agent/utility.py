from .prereq import distance_to_prereqs


class Utility():
    def __init__(self, utility_funcs):
        self.ufuncs = utility_funcs

    def __call__(self, state):
        """computes utility for a state"""
        utility = 0
        for attr, value in state.items():
            if attr in self.ufuncs:
                utility += self.ufuncs[attr](state[attr])
        return utility

    @profile
    def utility(self, curr_state, state):
        """compute the utility for a state change"""
        utility = 0
        for attr, value in state.items():
            if attr in self.ufuncs:
                new_state_utility = self.ufuncs[attr](value)
                current_state_utility = self.ufuncs[attr](curr_state[attr])
                utility += new_state_utility - current_state_utility
        return utility

    def expected_utility(self, state, outcomes):
        """computes expected utility of going from
        a given state to a set of possible outcomes"""
        eu = 0
        for state_, prob in outcomes.states(state):
            eu += prob * self.utility(state, state_)
        return eu

    def utility_for_goal(self, state, goal):
        """compute the utility for a state in relation to a goal.
        this is meant to capture the following:
            - the closer a state is to a goal, the higher its utility
            - its utility is higher if accomplishing the goal has a higher expected utility
            - its utility is higher if failing the goal has a higher expected cost
        """
        # for a non-zero denominators
        eps = 1e-10

        # estimated "distance" to the achieving goal prerequisites
        dist = distance_to_prereqs(state, goal.prereqs)

        # expected utility of achieving the goal
        expu = self.expected_utility(state, goal.outcomes)

        # time left until goal failure (temporal discounting)
        if goal.time is not None:
            tempd = 1/(goal.time + eps)
            # expected failure state and utility
            expfs = goal.failures.expected_state(state)
            expfu = self.utility(state, expfs)

        # if there is no goal time sensitivity,
        # we assume there are no failure states (should this change?)
        else:
            expfu, tempd = 0, 0

        return (1/(dist + eps)) * (expu - (expfu * tempd))
