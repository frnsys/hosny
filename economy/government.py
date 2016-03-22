from cess.agent.learn import QLearner


class Government():
    def __init__(self, tax_rate, welfare, tax_rate_increment, welfare_increment):
        self.cash = 0
        self.tax_rate = tax_rate
        self.tax_rate_increment = tax_rate_increment
        self.welfare = welfare
        self.welfare_increment = welfare_increment

        # all states map to the same actions
        action_ids = [i for i in range(len(self.actions))]
        states_actions = {s: action_ids for s in range(3)}
        self.learner = QLearner(states_actions, self.reward, discount=0.5, explore=0.01, learning_rate=0.5)

        # keep track of previous step's quality of life for comparison
        self.prev_qol = 0

    @property
    def actions(self):
        """these actions are possible from any state"""
        return [
            {'tax_rate': self.tax_rate_increment},
            {'tax_rate': -self.tax_rate_increment},
            {'tax_rate': self.tax_rate_increment, 'welfare': self.welfare_increment},
            {'tax_rate': self.tax_rate_increment, 'welfare': -self.welfare_increment},
            {'tax_rate': -self.tax_rate_increment, 'welfare': self.welfare_increment},
            {'tax_rate': -self.tax_rate_increment, 'welfare': -self.welfare_increment}
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

    def adjust(self, households):
        action = self.learner.choose_action(self.current_state(households))
        action = self.actions[action]
        self.tax_rate = min(1, max(0, self.tax_rate + action.get('tax_rate', 0)))
        self.welfare = min(max(0, self.welfare + action.get('welfare', 0)), self.cash/sum(len(h.people) for h in households))
        self.prev_qol = sum(h.quality_of_life for h in households)/len(households)
