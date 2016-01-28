import math
import numpy as np
from .utility import utility


def expand_graph(fringe, succ_func):
    """exhaustively expand a search graph"""
    while fringe:
        path = fringe.pop()
        yield path
        node = path[-1]
        fringe.extend(reversed([path + [child] for child in succ_func(node)]))


def heuristic(state, goal):
    """an admissible heuristic never overestimates the distance to the goal"""

    return 0 # TEMPORARY

    # TODO come up with a good admissible heuristic
    sorted_keys = sorted(goal)

    # vectorize
    goal_vec = np.array([goal[k] for k in sorted_keys])
    curr_vec = np.array([state[k] for k in sorted_keys])

    # normalize
    curr_vec = curr_vec/goal_vec
    goal_vec = goal_vec/goal_vec

    # euclidean distance
    return np.linalg.norm(goal_vec-curr_vec)


def distance(from_state, to_state, action):
    """we define distance so that we minimize time spent
    and maximize expected utility, but prioritize expected utility"""
    time = action.hours
    util = utility(from_state, to_state)
    if util < 0:
        return time * pow(util, 2)
    else:
        return time * 0.1 * (math.tanh(-util) + 1)


def satisfied(state, goal):
    """check that a goal is satisfied by the specified state"""
    return all(pred(state[k]) for k, pred in goal.items())


def _ida(agent, path, goal, length, depth, succ_func, seen):
    """subroutine for iterative deepening A*"""
    _, node = path[-1]

    f = length + heuristic(node, goal)
    if f > depth: return f, None

    if satisfied(node, goal):
        return f, path

    # extended list filtering:
    # skip nodes we have already seen
    nhash = hash(frozenset(node.items()))
    if nhash in seen: return f, None
    seen.add(nhash)

    minimum = float('inf')
    best_path = None
    # for now ignore world time constraints
    for action, child in succ_func(node):
        # g(n) = distance(n)
        thresh, new_path = _ida(agent,
                                path + [(action, child)],
                                goal,
                                length + distance(node, child, action),
                                depth, succ_func, seen)
        if new_path is not None and thresh < minimum:
            minimum = thresh
            best_path = new_path
    return minimum, best_path


def ida(agent, root, goal, succ_func):
    """iterative deepening A*"""
    solution = None
    depth = heuristic(root, goal)
    while solution is None:
        _, solution = _ida(agent, [(None, root)], goal, 0, depth, succ_func, set())
        depth += 1
    return solution
