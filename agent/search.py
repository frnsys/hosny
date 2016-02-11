import math


class Planner():
    def __init__(self, succ_func, util_func):
        self.succ_func = succ_func
        self.util_func = util_func

    def heuristic(self, node, goal):
        """an admissible heuristic never overestimates the distance to the goal"""

        # TODO come up with a good admissible heuristic
        return 0 # TEMPORARY

    def distance(self, from_node, to_node, action):
        """we define distance so that we minimize cost
        and maximize expected utility, but prioritize expected utility"""
        from_state, _ = from_node
        to_state, _ = to_node
        cost = action.cost()
        util = self.util_func(from_state, to_state)
        if util < 0:
            return cost * pow(util, 2)
        else:
            return cost * 0.1 * (math.tanh(-util) + 1)

    def _ida(self, agent, path, goal, length, depth, seen):
        """subroutine for iterative deepening A*"""
        _, node = path[-1]

        f = length + self.heuristic(node, goal)
        if f > depth: return f, None

        state, _ = node
        if goal.satisfied(state):
            return f, path


        # extended list filtering:
        # skip nodes we have already seen
        nhash = hash(frozenset(node.items()))
        if nhash in seen: return f, None
        seen.add(nhash)

        minimum = float('inf')
        best_path = None
        for action, child in self.succ_func(node):
            # g(n) = distance(n)
            thresh, new_path = self._ida(agent,
                                         path + [(action, child)],
                                         goal,
                                         length + self.distance(node, child, action),
                                         depth, seen)
            if new_path is not None and thresh < minimum:
                minimum = thresh
                best_path = new_path
        return minimum, best_path

    def ida(self, agent, root, goal):
        """iterative deepening A*"""
        solution = None
        depth = self.heuristic(root, goal)
        while solution is None:
            _, solution = self._ida(agent, [(None, root)], goal, 0, depth, set())
            depth += 1
        return solution


def hill_climbing(root, succ_func, valid_func, depth):
    """always choose the best node next.
    this only terminates if the succ_func eventually returns nothing.
    assumes the succ_func returns child nodes in descending order of value.
    this may not find the highest-scoring path (since it's possible that the highest-scoring path
    goes through a low-scoring node), but this saves _a lot_ of time"""
    new_goals = set()
    seen = set()
    fringe = [[root]]
    while fringe:
        path = fringe.pop(0)
        node = path[-1]
        act, (state, goals) = node

        # extended list filtering:
        # skip nodes we have already seen
        nhash = hash(frozenset(state.items()))
        if nhash in seen: continue
        seen.add(nhash)

        # check that the next move is valid,
        # given the past node,
        # if not, save as a goal and backtrack
        if len(path) >= 2 and not valid_func(node, path[-2]):
            new_goals.add(act)
            continue

        # if we terminate at a certain depth, break when we reach it
        if depth is not None and len(path) > depth:
            break

        succs = succ_func(node)
        # if no more successors, we're done
        if not succs:
            break

        # assumed that these are best-ordered successors
        fringe = [path + [succ] for succ in succs] + fringe

    # remove the root
    path.pop(0)
    return path, new_goals
