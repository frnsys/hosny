import unittest
import operator
import agent.utility as util
from agent.action import Prereq, Outcome, Goal


class AgentTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_prereqs_satisfied(self):
        prereq = Prereq(operator.lt, 10)
        self.assertTrue(prereq(1))
        self.assertFalse(prereq(11))

    def test_distance_to_prereqs(self):
        prereq = Prereq(operator.lt, 10)
        prereqs = {'sup': prereq}

        state = {'sup': 1}
        self.assertEqual(util.distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 10}
        self.assertEqual(util.distance_to_prereqs(state, prereqs), 0.0)

        state = {'sup': 20}
        self.assertTrue(util.distance_to_prereqs(state, prereqs) > 0.0)

    def test_state_utility_for_goal(self):
        goal = Goal(
            prereqs={
                'sup': Prereq(operator.lt, 10)
            },
            outcomes=[
                Outcome({'cash': 1000}, 1.)
            ],
            failures=[],
            time=None)

        # closer to the goal
        state = {'sup': 11, 'cash':0}
        util1 = util.utility_for_goal(state, goal)

        # further from the goal
        state = {'sup': 20, 'cash':0}
        util2 = util.utility_for_goal(state, goal)

        self.assertTrue(util1 > util2)
