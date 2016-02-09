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
        util = 1
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

    @profile
    def expand_graph(self, fringe, max_depth=None):
        """exhaustively expand a search graph"""
        while fringe:
            path = fringe.pop()
            yield path
            if max_depth is None or len(path) < max_depth:
                node = path[-1]
                fringe.extend(reversed([path + [child] for child in self.succ_func(node)]))
