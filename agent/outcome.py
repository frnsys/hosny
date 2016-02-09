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

    @profile
    def resolve(self, state):
        """choose a random outcome, apply to the state,
        and return the new state"""
        update = random_choice((u, p) for u, p in self(state))
        state = self._update(state, update)

        # only when resolving do we apply the special state function
        if '~' in update:
            state.update(update['~'](state))
        return state

    def states(self, state):
        """yield all outcome states, with probabilities"""
        for o, p in self(state):
            yield self._update(o, state, expected=True), p

    def expected_state(self, state):
        """computes an expected state from a given state
        over a set of possible outcomes"""
        expstate = defaultdict(list)
        for update, prob in self(state):
            outcome_state = self._update(state, update, expected=True)
            for k, v in outcome_state.items():
                try:
                    expstate[k].append(v * prob)

                # for non-numerical types
                except TypeError:
                    expstate[k].append((v, prob))

        for k in expstate.keys():
            try:
                expstate[k] = sum(expstate[k])

            # non-numerical types: most likely value rather than the mean
            except TypeError:
                expstate[k] = max(expstate[k], key=lambda x: x[1])[0]
        return dict(expstate)

    @profile
    def _update(self, state, update, expected=False):
        """generates a new state based on the specified update dict"""
        state = state.copy()
        for k, v in update.items():
            # ignore keys not in state
            if k not in state:
                continue

            # v can be a callable, taking the state,
            # or an int/float
            try:
                val, exp = v(state)
                state[k] += (exp if expected else val)
            except TypeError:
                state[k] += v
        return state
