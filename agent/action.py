from .outcome import Outcomes


class PrereqsUnsatisfied(Exception):
    pass


class Action():
    """an action an agent can take. actions has a distribution
    of possible outcomes and may have prerequisites"""
    def __init__(self, name, prereqs, outcomes):
        self.name = name
        self.prereqs = prereqs
        self.outcomes = Outcomes(*outcomes)

    def __repr__(self):
        return 'Action({})'.format(self.name)

    def __call__(self, state):
        """complete this action (if its prereqs are satisfied),
        returning an outcome state"""
        if not self.satisfied(state):
            raise PrereqsUnsatisfied
        return self.outcomes.resolve(state)

    def satisfied(self, state):
        """check that the action's prereqs are satisfied by the specified state"""
        return all(prereq(state[k]) for k, prereq in self.prereqs.items())

    def cost(self):
        return 1 # TODO TEMP

    def expected_state(self, state):
        return self.outcomes.expected_state(state)


class Goal(Action):
    """a goal that can timeout and fail"""
    def __init__(self, name, prereqs, outcomes, failures=None, time=None):
        super().__init__(name, prereqs, outcomes)
        self.time = time

        if failures is not None:
            self.failures = Outcomes(*failures)
        else:
            self.failures = None

    def __repr__(self):
        return 'Goal({})'.format(self.name)

    def tick(self):
        if self.time is not None:
            self.time -= 1

    def fail(self, state):
        """fail to complete this goal,
        returning the resulting state"""
        if self.failures is not None:
            return self.failures.resolve(state)
        return state

    def expected_failure_state(self, state):
        if self.failures is not None:
            return self.failures.expected_state(state)
        return state
