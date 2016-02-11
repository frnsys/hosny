import unittest
from agent import outcome


class OutcomeTests(unittest.TestCase):
    def test_probabilities(self):
        state = {'cash': 0}
        updates = [{'cash': 1000}, {'cash': 2000}]
        dist = [0.8, 0.2]
        update_dist = outcome.update_dist(state, updates, dist)
        self.assertEqual(
            [(u, p) for u, p in update_dist],
            [(u, p) for u, p in zip(updates, dist)]
        )

    def test_probabilities_lambda(self):
        state = {'cash': 0}
        updates = [{'cash': 1000}, {'cash': 2000}]
        dist = lambda x: [1/3, 2/3]
        update_dist = outcome.update_dist(state, updates, dist)
        self.assertEqual(
            [(u, p) for u, p in update_dist],
            [({'cash': 1000}, 1/3), ({'cash': 2000}, 2/3)]
        )

    def test_expected_state(self):
        state = {'cash': 0}
        updates = [{'cash': 1000}, {'cash': 2000}]
        dist = [0.5, 0.5]
        exp_state = outcome.expected_state(state, updates, dist)
        self.assertEqual(exp_state, {'cash': 1500})

    def test_states(self):
        state = {'cash': 100}
        updates = [{'cash': 1000}, {'cash': 2000}]
        dist = [0.8, 0.2]
        outcome_dist = outcome.outcome_dist(state, updates, dist)
        self.assertEqual(
            [(u, p) for u, p in outcome_dist],
            [({'cash': 1100}, 0.8), ({'cash': 2100}, 0.2)]
        )

