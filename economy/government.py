from cess.util import random_choice
from cess.agent.learn import QLearner

TAX_RATE = 0.3
TAX_RATE_INCREMENT = 0.01
WELFARE_INCREMENT = 10


class Government():
    def __init__(self):
        self.cash = 0
        self.tax_rate = TAX_RATE
        self.welfare = 0

        # all states map to the same actions
        action_ids = [i for i in range(len(self.actions))]
        states_actions = {s: action_ids for s in range(3)}
        self.learner = QLearner(states_actions, self.reward, discount=0.5, explore=0.01, learning_rate=0.5)

        self.prev_qol = 0

    @property
    def actions(self):
        """these actions are possible from any state"""
        return [
            {'tax_rate': TAX_RATE_INCREMENT},
            {'tax_rate': -TAX_RATE_INCREMENT},
            {'tax_rate': TAX_RATE_INCREMENT, 'welfare': WELFARE_INCREMENT},
            {'tax_rate': TAX_RATE_INCREMENT, 'welfare': -WELFARE_INCREMENT},
            {'tax_rate': -TAX_RATE_INCREMENT, 'welfare': WELFARE_INCREMENT},
            {'tax_rate': -TAX_RATE_INCREMENT, 'welfare': -WELFARE_INCREMENT}
        ]

    def current_state(self, households):
        """represent as a discrete state"""
        qol = sum(h.quality_of_life for h in households)/len(households)

        if qol <= 0:
            return 0
        elif qol > 0 and qol - self.prev_qol <= 0:
            return 1
        elif qol > 0 and qol - self.prev_qol > 0:
            return 2

    def reward(self, state):
        """the discrete states we map to are the reward values, so just return that"""
        return state

    def make_decisions(self, households):
        # adjust production
        action = self.learner.choose_action(self.current_state(households))
        action = self.actions[action]
        self.tax_rate = min(1, max(0, self.tax_rate + action.get('tax_rate', 0)))
        self.welfare = max(0, self.welfare + action.get('welfare', 0))
