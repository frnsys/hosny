import unittest
import operator
from agent.action import Goal
from agent.prereq import Prereq
from agent.utility import Utility
from agent.outcome import Outcomes

utility_funcs = {
    'cash': lambda x: x
}


class UtilityTests(unittest.TestCase):
    def test_utility(self):
        util = Utility(utility_funcs)
        state = {'cash': 0}
        to_state = {'cash': 1000}
        util = util.utility(state, to_state)
        self.assertEqual(util, 1000)

    def test_expected_utility(self):
        util = Utility(utility_funcs)
        state = {'cash': 0}
        outcomes = Outcomes([{'cash': 1000}, {'cash': 2000}], [0.5, 0.5])
        exp_util = util.expected_utility(state, outcomes)
        self.assertEqual(exp_util, 1500)

    def test_state_utility_for_goal(self):
        goal = Goal(
            'test_goal',
            prereqs={'sup': Prereq(operator.lt, 10)},
            outcomes=([{'cash': 1000}], [1.]),
            failures=None,
            time=None)
        util = Utility(utility_funcs)

        # closer to the goal
        state = {'sup': 11, 'cash':0}
        util1 = util.utility_for_goal(state, goal)

        # further from the goal
        state = {'sup': 20, 'cash':0}
        util2 = util.utility_for_goal(state, goal)

        self.assertTrue(util1 > util2)
