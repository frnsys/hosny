import unittest
import operator
from agent import Agent, Action, Goal, Prereq


class AgentTests(unittest.TestCase):
    def test_score_plan(self):
        utility_funcs = {
            'cash': lambda x: x
        }
        action = Action('work', {}, ([{'cash': 100}], [1.]))
        goal = Goal('money', {'cash': Prereq(operator.ge, 200)}, ([{'cash': 1000}], [1.]))
        agent = Agent({'cash':0}, [action], [goal], utility_funcs, {})

        path_a = [(action, ({'cash': -100}, []))]
        path_b = [(action, ({'cash': 100}, []))]
        path_c = [(action, ({'cash': 200}, []))]
        path_d = [(action, ({'cash': 300}, []))]

        self.assertTrue(agent.score_plan(path_a) < agent.score_plan(path_b))
        self.assertTrue(agent.score_plan(path_b) < agent.score_plan(path_c))
        self.assertTrue(agent.score_plan(path_c) < agent.score_plan(path_d))

    def test_make_plans(self):
        utility_funcs = {
            'cash': lambda x: x
        }
        action = Action('work', {}, ([{'cash': 100}, {'cash': 50}], [0.5, 0.5]))
        goal = Goal('money', {'cash': Prereq(operator.ge, 200)}, ([{'cash': 1000}], [1.]))
        agent = Agent({'cash':0}, [action], [goal], utility_funcs, {})
        plans = agent.make_plans(agent.state, agent.goals, depth=3)
        expected_plans = [
            [(action, ({'cash': 75.0}, {goal})), (action, ({'cash': 150.0}, {goal})), (action, ({'cash': 225.0}, {goal}))],
            [(action, ({'cash': 75.0}, {goal})), (action, ({'cash': 150.0}, {goal}))],
            [(action, ({'cash': 75.0}, {goal}))]]
        self.assertEqual(plans, expected_plans)

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
