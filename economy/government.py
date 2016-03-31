import random
from cess import Agent
from enum import IntEnum
from cess.agent.learn import QLearner
from .firms import ConsumerGoodFirm, CapitalEquipmentFirm, RawMaterialFirm, Hospital

industries = {
    'consumer': ConsumerGoodFirm,
    'equip': CapitalEquipmentFirm,
    'material': RawMaterialFirm,
    'hospital': Hospital
}


class Government(Agent):
    def __init__(self, tax_rate, welfare, tax_rate_increment, welfare_increment, starting_welfare_req):
        self._state = {'cash': 0}
        self.tax_rate = tax_rate
        self.tax_rate_increment = tax_rate_increment
        self.welfare = welfare
        self.welfare_increment = welfare_increment
        self.welfare_req = starting_welfare_req
        self.subsidies = {
            ConsumerGoodFirm: 0,
            CapitalEquipmentFirm: 0,
            RawMaterialFirm: 0,
            Hospital: 0
        }
        self.altruism = 0

        # all states map to the same actions
        action_ids = [i for i in range(len(self.actions))]
        states_actions = {s: action_ids for s in range(3)}
        self.learner = QLearner(states_actions, self.reward, discount=0.5, explore=0.01, learning_rate=0.5)

        # keep track of previous step's quality of life for comparison
        self.prev_qol = 0

    @property
    def cash(self):
        return self._state['cash']

    @cash.setter
    def cash(self, value):
        self._state['cash'] = value

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
        qol = sum(h.quality_of_life for h in households)/len(households) if households else 0

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
        max_per_person = self.cash/sum(len(h.people) for h in households if h.income <= self.welfare_req) if households else 0
        self.welfare = min(max(0, self.welfare + action.get('welfare', 0)), max_per_person)
        self.prev_qol = sum(h.quality_of_life for h in households)/len(households) if households else 0

    def apply_proposal(self, proposal, world):
        t = proposal['type']
        v = float(proposal['value']) if proposal.get('value') is not None else None
        if t == ProposalType.nationalize.name:
            industry = proposal['target']
            firm = random.choice(world.firms_of_type(industries[industry]))
            firm.change_owner(self)
        elif t == ProposalType.privatize.name:
            industry = proposal['target']
            firm = random.choice(world.firms_of_type(industries[industry]))

            # randomly pick new owner
            # we pick the person with the most money who does not already have a firm
            candidates = sorted([p for p in world.people if not p._state['firm_owner']], key=lambda p: p._state['cash'], reverse=True)
            new_owner = candidates[0]
            firm.change_owner(new_owner)
        elif t == ProposalType.tax_rate.name:
            self.tax_rate = v
        elif t == ProposalType.welfare.name:
            self.welfare = v
        elif t == ProposalType.welfare_req.name:
            self.welfare_req = v
        elif t == ProposalType.subsidy.name:
            self.subsidies[industries[proposal['target']]] = v

    def proposal_options(self, world):
        options = [{
            'type': ProposalType.tax_rate.name,
            'name': 'adjust tax rate',
            'description': 'Adjust the tax rate for all income and corporate profits',
            'values': [0, 1],
            'targets': None,
            'value': self.tax_rate
        }, {
            'type': ProposalType.welfare.name,
            'name': 'adjust welfare',
            'description': 'Set the amount of cash distributed to every citizen who makes less than the welfare requirement',
            'values': [0, None],
            'targets': None,
            'value': self.welfare
        }, {
            'type': ProposalType.welfare_req.name,
            'name': 'adjust welfare income threshold',
            'description': 'Citizens who make less than this income will receive welfare',
            'values': [0, None],
            'targets': None,
            'value': self.welfare_req
        }, {
            'type': ProposalType.subsidy.name,
            'name': 'adjust industry subsidy',
            'description': 'Set the amount of cash government gives a particular industry',
            'values': [0, None],
            'targets': list(industries.keys()),
            'value': None
        }]

        private_industries = self.filter_industries(world, public=False)
        public_industries = self.filter_industries(world, public=True)
        if public_industries:
            options.append({
                'type': ProposalType.privatize.name,
                'name': 'privatize a public firm',
                'description': 'Release a national firm into private management',
                'values': None,
                'targets': public_industries,
                'value': None
            })
        if private_industries:
            options.append({
                'type': ProposalType.nationalize.name,
                'name': 'nationalize a private firm',
                'description': 'Put a private firm into the control of the people',
                'values': None,
                'targets': private_industries,
                'value': None
            })

        return options

    def filter_industries(self, world, public=False):
        """return industries that have firms in them"""
        return [ind for ind, typ in industries.items() if [f for f in world.firms_of_type(typ) if f.public == public]]

    def as_json(self):
        return {
            'tax_rate': self.tax_rate,
            'welfare': self.welfare,
            'welfare_req': self.welfare_req,
            'subsidies': {k.__name__: v for k, v in self.subsidies.items()}
        }


class ProposalType(IntEnum):
    nationalize = 0
    privatize   = 1
    tax_rate    = 2
    welfare     = 3
    welfare_req = 4
    subsidy     = 5
