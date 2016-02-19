from .outcome import resolve_outcomes, expected_state, outcome_dist


class PrereqsUnsatisfied(Exception):
    pass


class Action():
    """an action an agent can take. actions has a distribution
    of possible outcomes and may have prerequisites"""
    def __init__(self, name, prereqs, outcomes):
        """`outcomes` is a tuple of `(updates, dist)`,
        where `updates` is a list of update dictionaries and `dist` is
        either a list of probabilities for each corresponding state update,
        or a callable which returns such a list of probabilities"""
        self.name = name
        self.prereqs = prereqs
        self.updates, self.dist = outcomes

    def __repr__(self):
        return 'Action({})'.format(self.name)

    def __call__(self, state):
        """complete this action (if its prereqs are satisfied),
        returning an outcome state"""
        if not self.satisfied(state):
            raise PrereqsUnsatisfied
        return resolve_outcomes(state, self.updates, self.dist)

    def satisfied(self, state):
        """check that the action's prereqs are satisfied by the specified state"""
        return all(prereq(state[k]) for k, prereq in self.prereqs.items())

    def cost(self):
        return 1 # TODO TEMP

    def expected_state(self, state):
        return expected_state(state, self.updates, self.dist)

    def outcomes(self, state):
        return outcome_dist(state, self.updates, self.dist)


class Goal(Action):
    """a goal that can timeout and fail"""
    def __init__(self, name, prereqs, outcomes, failures=None, time=None):
        super().__init__(name, prereqs, outcomes)
        self.time = time

        if failures is None:
            failures = ([{}], [1.])
        self.fail_updates, self.fail_dist = failures

    def __repr__(self):
        return 'Goal({})'.format(self.name)

    def tick(self):
        if self.time is not None:
            self.time -= 1

    def fail(self, state):
        """fail to complete this goal, returning the resulting state"""
        return resolve_outcomes(state, self.fail_updates, self.fail_dist)

    def expected_failure_state(self, state):
        return expected_state(state, self.fail_updates, self.fail_dist)
