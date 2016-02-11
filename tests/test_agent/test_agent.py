import unittest
import operator
from agent import Agent, Action, Goal, Prereq


class AgentTests(unittest.TestCase):
    def test_score_successor(self):
        utility_funcs = {
            'cash': lambda x: x
        }
        action = Action('work', {}, ([{'cash': 100}], [1.]))
        goal = Goal('money', {'cash': Prereq(operator.ge, 200)}, ([{'cash': 1000}], [1.]))
        agent = Agent({'cash':0}, [action], [goal], utility_funcs, {})

        from_state = {'cash': 0}
        state_a = {'cash': -100}
        state_b = {'cash': 100}
        state_c = {'cash': 200}
        state_d = {'cash': 300}

        self.assertTrue(agent._score_successor(from_state, state_a) < agent._score_successor(from_state, state_b))
        self.assertTrue(agent._score_successor(from_state, state_b) < agent._score_successor(from_state, state_c))
        self.assertTrue(agent._score_successor(from_state, state_c) < agent._score_successor(from_state, state_d))

    def test_plan(self):
        utility_funcs = {
            'cash': lambda x: x
        }
        action = Action('work', {}, ([{'cash': 100}, {'cash': 50}], [0.5, 0.5]))

        # an action not achievable immediately, should become a goal
        action_goal = Action('hire help', {'cash': Prereq(operator.ge, 200)}, ([{'cash': 1000}], [1.]))
        goal = Goal('money', {'cash': Prereq(operator.ge, 200)}, ([{'cash': 1000}], [1.]))

        agent = Agent({'cash':0}, [action, action_goal], [goal], utility_funcs, {})
        plan, goals = agent.plan(agent.state, agent.goals, depth=3)
        expected_plan = [(action, ({'cash': 75.0}, {goal})), (action, ({'cash': 150.0}, {goal})), (action, ({'cash': 225.0}, {goal}))]

        # goals should contain the desired, but not yet satisfiable, action
        self.assertEqual(goals, set([goal, action_goal]))

        # returned plan should not contain unsatisfiable actions
        self.assertEqual(plan, expected_plan)

    def test_state(self):
        var_constraints = {
            'stress': [0., 1.]
        }

        agent = Agent({'stress':0.5}, [], [], {}, var_constraints)
        self.assertEqual(agent['stress'], 0.5)

        agent['stress'] = 100
        self.assertEqual(agent['stress'], 1.)

        agent['stress'] = -100
        self.assertEqual(agent['stress'], 0.)

        agent.state = {'stress': 100}
        self.assertEqual(agent['stress'], 1.)
