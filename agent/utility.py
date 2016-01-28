import math
import numpy as np
from collections import defaultdict


# utility functions
# note that infinities do not work well here;
# they make it harder to compare utilities
utility_funcs = {
    'stress': lambda x: -(2**x) if x > 1 else 0.5 * math.log(-x+1+1e12) + 0.1,
    'cash': lambda x: x
}


def utility(curr_state, state):
    """compute the utility for a state change"""
    utility = 0
    for attr, value in state.items():
        if attr in utility_funcs:
            new_state_utility = utility_funcs[attr](value)
            current_state_utility = utility_funcs[attr](curr_state[attr])
            utility += new_state_utility - current_state_utility
    return utility


def expected_utility(state, outcomes):
    """computes expected utility of going from
    a given state to a set of possible outcomes"""
    eu = 0
    for outcome in outcomes:
        eu += outcome.prob * utility(state, outcome(state))
    return eu


def expected_state(state, outcomes):
    """computes an expected state from a given state
    over a set of possible outcomes"""
    expstate = defaultdict(list)
    for outcome in outcomes:
        outcome_state = outcome(state)
        for k, v in outcome_state.items():
            expstate[k].append(v * outcome.prob)
    for k in expstate.keys():
        expstate[k] = sum(expstate[k])
    return dict(expstate)


def utility_for_goal(state, goal):
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
    expu = expected_utility(state, goal.outcomes)

    # time left until goal failure (temporal discounting)
    if goal.time is not None:
        tempd = 1/(goal.time + eps)
        # expected failure state and utility
        expfs = expected_state(state, goal.failures)
        expfu = utility(state, expfs)

    # if there is no goal time sensitivity,
    # we assume there are no failure states (should this change?)
    else:
        expfu, tempd = 0, 0

    return (1/(dist + eps)) * (expu - (expfu * tempd))


def distance_to_prereqs(state, prereqs):
    """(euclidean) distance of a state to a set of prerequisites"""
    # vectorize
    goal_vec = []
    curr_vec = []
    for k in prereqs.keys():
        pre = prereqs[k]

        # goal vector just consists of target values
        goal_vec.append(pre.target)

        # if the state value satisfies the prereq,
        # set it to be equal to the target value
        val = state[k]
        if pre(val):
            curr_vec.append(pre.target)
        else:
            curr_vec.append(val)
    goal_vec = np.array(goal_vec)
    curr_vec = np.array(curr_vec)

    # normalize
    curr_vec = curr_vec/goal_vec
    goal_vec = goal_vec/goal_vec

    # euclidean distance
    return np.linalg.norm(goal_vec-curr_vec)
