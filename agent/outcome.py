from collections import defaultdict
from util import random_choice


class Outcomes():
    def __init__(self, updates, dist):
        """`updates` is a list of update dictionaries and `dist` is
        either a list of probabilities for each corresponding state update,
        or a callable which returns such a list of probabilities"""
        self.updates = updates
        self.dist = dist

    def __call__(self, state):
        """yields outcomes updates and their probability"""
        dist = self.dist
        updates = self.updates

        if not isinstance(dist, list):
            dist = dist(state)

        # add missing mass if necessary
        # with a "no effect" outcome
        mass = sum(dist)
        if mass < 1:
            updates.append({})
            dist.append(1 - mass)

        for u, p in zip(updates, dist):
            yield u, p

    def resolve(self, state):
        """choose a random outcome, apply to the state,
        and return the new state"""
        update = random_choice((u, p) for u, p in self(state))
        return self._update(state, update)

    def states(self, state):
        """yield all outcome states, with probabilities"""
        for o, p in self(state):
            yield self._update(o, state), p

    def expected_state(self, state):
        """computes an expected state from a given state
        over a set of possible outcomes"""
        expstate = defaultdict(list)
        for update, prob in self(state):
            outcome_state = self._update(state, update)
            for k, v in outcome_state.items():
                expstate[k].append(v * prob)
        for k in expstate.keys():
            expstate[k] = sum(expstate[k])
        return dict(expstate)

    def _update(self, state, update):
        """generates a new state based on the specified update dict"""
        state = state.copy()
        for k, v in update.items():
            if k not in state:
                continue

            # v can be a callable, taking the state,
            # or an int/float
            try:
                state[k] += v(state)
            except TypeError:
                state[k] += v
        return state
