import unittest
import operator
from agent.prereq import Prereq, distance_to_prereqs


class PrereqTests(unittest.TestCase):
    def test_prereqs_satisfied(self):
        prereq = Prereq(operator.lt, 10)
        self.assertTrue(prereq(1))
        self.assertFalse(prereq(11))

    def test_distance_to_prereqs(self):
        prereq = Prereq(operator.lt, 10)
        prereqs = {'sup': prereq}

        state = {'sup': 1}
        self.assertEqual(distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 10}
        self.assertEqual(distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 20}
        self.assertTrue(distance_to_prereqs(state, prereqs) > 0.0)

    def test_distance_to_prereqs_boolean(self):
        prereq = Prereq(operator.eq, True)
        prereqs = {'sup': prereq}

        state = {'sup': True}
        self.assertEqual(distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': False}
        self.assertTrue(distance_to_prereqs(state, prereqs) > 0.0)

    def test_and_prereqs_satisfied(self):
        prereq = (Prereq(operator.lt, 10) & Prereq(operator.gt, 5))
        self.assertTrue(prereq(6))
        self.assertFalse(prereq(1))
        self.assertFalse(prereq(11))

    def test_distance_to_and_prereqs(self):
        prereq = (Prereq(operator.lt, 10) & Prereq(operator.gt, 5))
        prereqs = {'sup': prereq}

        state = {'sup': 6}
        self.assertEqual(distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 1}
        self.assertTrue(distance_to_prereqs(state, prereqs) > 0.0)

        state = {'sup': 11}
        self.assertTrue(distance_to_prereqs(state, prereqs) > 0.0)

    def test_or_prereqs_satisfied(self):
        prereq = (Prereq(operator.lt, 5) | Prereq(operator.gt, 10))
        self.assertTrue(prereq(1))
        self.assertTrue(prereq(11))
        self.assertFalse(prereq(6))

    def test_distance_to_d_prereqs(self):
        prereq = (Prereq(operator.lt, 5) | Prereq(operator.gt, 10))
        prereqs = {'sup': prereq}

        state = {'sup': 1}
        self.assertEqual(distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 11}
        self.assertEqual(distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 6}
        self.assertTrue(distance_to_prereqs(state, prereqs) > 0.0)
