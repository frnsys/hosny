from .prereq import distance_to_prereqs


# def utility(ufuncs, state):
    # """computes utility for a state"""
    # utility = 0
    # for attr, value in state.items():
        # if attr in ufuncs:
            # utility += ufuncs[attr](state[attr])
    # return utility


def utility(ufuncs, curr_state, state):
    """compute the utility for a state change"""
    utility = 0
    for attr, value in state.items():
        if attr in ufuncs:
            new_state_utility = ufuncs[attr](value)
            current_state_utility = ufuncs[attr](curr_state[attr])
            utility += new_state_utility - current_state_utility
    return utility


def expected_utility(ufuncs, state, outcomes):
    """computes expected utility of going from
    a given state to a set of possible outcomes"""
    eu = 0
    for state_, prob in outcomes:
        eu += prob * utility(ufuncs, state, state_)
    return eu


def goal_utility(ufuncs, state, goal):
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
    expu = expected_utility(ufuncs, state, goal.outcomes(state))

    # time left until goal failure (temporal discounting)
    if goal.time is not None:
        tempd = 1/(goal.time + eps)
        # expected failure state and utility
        expfs = goal.failures.expected_state(state)
        expfu = utility(ufuncs, state, expfs)

    # if there is no goal time sensitivity,
    # we assume there are no failure states (should this change?)
    else:
        expfu, tempd = 0, 0

    return (1/(dist + eps)) * (expu - (expfu * tempd))


def goals_utility(ufuncs, state, goals):
    """computes sum of utilities for a set of goals"""
    return sum(goal_utility(ufuncs, state, g) for g in goals)
