from mesa import Agent
from .search import Planner
from .utility import Utility
from .action import Action, Goal
from .prereq import Prereq


class Agent(Agent):
    """an (expected) utility maximizing agent,
    capable of managing long-term goals"""

    def __init__(self, state, actions, goals, utility_funcs, ranges, dtypes, debug=True):
        self.state = state
        self.goals = set(goals)
        self.actions = actions
        self.utility = Utility(utility_funcs)
        self.planner = Planner(self._succ_func, self.utility.utility)
        self.ranges = ranges
        self.dtypes = dtypes
        self.debug = debug

    def actions_for_state(self, state):
        """the agent's possible actions
        for a given agent state -
        you probably want to override this"""
        for action in self.actions:
            yield action

    def successors(self, state, goals):
        """the agent's possible successors (expected states)
        for a given agent state"""
        actions = self.actions_for_state(state)

        # compute expected states
        succs = []
        for action in actions:
            expstate = self._expected_state(action, state)
            succs.append((action, (expstate, goals)))

        for goal in goals:
            if goal.satisfied(state):
                expstate = self._expected_state(goal, state)
                remaining_goals = goals.copy()
                remaining_goals.remove(goal)
                succs.append((action, (expstate, remaining_goals)))

        # sort by expected utility, desc
        succs = sorted(succs, key=lambda s: self.utility.utility(state, s[1][0]), reverse=True)
        return succs

    def subplan(self, state, goal):
        """create a subplan to achieve a goal;
        i.e. the prerequisites for an action"""
        return self.planner.ida(self, state, goal.as_action())

    def _succ_func(self, node):
        act, (state, goals) = node
        return self.successors(state, goals)

    @profile
    def score_plan(self, path):
        """good paths get agents closer to high-priority goals
        have a good average expected utility across all states"""
        first_action, (first_state, _) = path[0]
        final_action, (final_state, _) = path[-1]

        final_state_utility = self.utility.utility(self.state, final_state) + \
            sum(self.utility.utility_for_goal(final_state, g) for g in self.goals)

        #if self.debug:
            #print('-----------------------------')
            #first_action, (first_state, _) = path[0]
            #print('first action:', first_action)
            #print('first state:', first_state)
            #print('-> start-to-state:', self.utility.utility(self.state, first_state))

            #for (a, (s, g)), (a_, (s_, g_)) in zip(path[:-1], path[1:-1]):
                #print('action:', a_)
                #print('state:', s_)
                #print('-> past-to-state:', self.utility.utility(s, s_))
                #print('-> start-to-state:', self.utility.utility(self.state, s))

            #print('final action:', final_action)
            #print('final state:', final_state)
            #print('-> fs-score:', final_state_utility)
            #print('-----------------------------')

        if path[:-1]:
            mean_exp_utility = sum([self.utility.utility(self.state, s) for a, (s, g) in path[:-1]])/len(path[:-1])
            return mean_exp_utility + final_state_utility
        else:
            return final_state_utility

    @profile
    def make_plans(self, state, goals, depth, predicate=None):
        """generate plans to the specified depth, from the specified starting state,
        sorted by scores (expected utility and closeness to goals)"""
        succs = self.successors(state, goals)

        # generate starting nodes
        plans = [[(action, node)] for action, node in succs]

        # generate the graph
        if predicate:
            plans = [path for path in self.planner.expand_graph(plans, max_depth=depth) if predicate(path)]
        else:
            plans = [path for path in self.planner.expand_graph(plans, max_depth=depth)]

        print('N_PLANS', len(plans))

        # rank plans by utilities of the expected states
        plans = sorted(plans, key=lambda p: self.score_plan(p), reverse=True)

        #if self.debug:
            #for plan in plans:
                #print(plan)
                #print('----->', self.score_plan(plan))

        return plans

    def plan(self, state, goals, depth, predicate=None):
        """selects a fully-satisfied plan
        from all possible plans, adding goals as necessary"""
        plan = []
        plans = self.make_plans(state, goals, depth, predicate)
        new_goals = goals.copy()
        while plans:
            satisfied = True
            last_state = state.copy()
            plan = plans.pop(0)
            for action, (s, g) in plan:
                if not action.satisfied(last_state):
                    new_goals.add(action)
                    satisfied = False
                    # this action can't be executed,
                    # so the state will not change -
                    # thus don't update last_state
                else:
                    last_state = s
            if satisfied:
                break
            else:
                # resort plans, since plan values may change
                # now that we have new goals
                plans = sorted(plans, key=lambda p: self.score_plan(p), reverse=True)
        return plan, new_goals

    def _expected_state(self, action, state):
        """computes expected state for an action/goal,
        attenuating it if necessary"""
        state = action.expected_state(state)
        return self._attenuate_state(state)

    def _attenuate_state(self, state):
        """attenuates a state to the agent's value ranges"""
        for k, v in state.items():
            # limit value to range if specified
            if k in self.ranges:
                mn, mx = self.ranges[k]
                if mn is not None: state[k] = max(mn, state[k])
                if mx is not None: state[k] = min(mx, state[k])
            if k in self.dtypes:
                state[k] = self.dtypes[k](state[k])
        return state
