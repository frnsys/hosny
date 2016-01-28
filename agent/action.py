

ranges = {
    'stress': [0, None]
}

class Prereq():
    """a prerequisite, e.g. for a goal or an action"""

    def __init__(self, comparator, target):
        """a comparator is a 2-arity predicate;
        the target is the value to compare to.
        generally you would use something like `operator.le`
        as a comparator."""
        self.target = target
        self.comparator = comparator

    def __call__(self, val):
        return self.comparator(val, self.target)


class Action():
    """an action an agent can take. actions has a distribution
    of possible outcomes and may have prerequisites. they may also
    have a cost"""

    def __init__(self, name, prereqs, outcomes, cost):
        assert(sum(o.prob for o in outcomes) == 1.)
        self.name = name
        self.prereqs = prereqs
        self.outcomes = outcomes
        self.cost = cost

    def __repr__(self):
        return 'Action({})'.format(self.name)


class Goal():
    """a goal is some state, defined by its prerequisites,
    with possible outcomes for completion. goals may be time-sensitive
    and yield failure outcomes as well"""

    def __init__(self, prereqs, outcomes=[], failures=[], time=None):
        self.prereqs = prereqs
        self.outcomes = outcomes

        # some goals may be time sensitive
        # in which they have failure outcomes
        self.time = time
        self.failures = failures

    def tick(self):
        if self.time is not None:
            self.time -= 1


class Outcome():
    """an outcome, with effects and a probability"""

    def __init__(self, effects, probability):
        """`effects` is a dict mapping attribute names
        to changes, e.g. {'happiness': -0.5}"""
        self.effects = effects
        self.prob = probability

    def __call__(self, state, expected=False):
        """generates a new state based on the specified updates"""
        state = state.copy()
        for k, v in self.effects.items():

            # `v` can be a scipy.stats distribution,
            try:
                if expected:
                    state[k] += v.mean()
                else:
                    state[k] += v.rvs()
            except AttributeError:
                state[k] += v

            # limit value to range if specified
            if k in ranges:
                mn, mx = ranges[k]
                if mn is not None: state[k] = max(mn, state[k])
                if mx is not None: state[k] = min(mx, state[k])
        return state
