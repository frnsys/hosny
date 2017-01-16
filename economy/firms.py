import json
import math
import logging
import numpy as np
import random
from scipy import optimize
from cess import Agent
from cess.util import random_choice
from cess.agent.learn import QLearner
from world.work import offer_prob, precompute_employment_dist

logger = logging.getLogger('simulation.firms')

with open('data/adjectives.txt', 'r') as f:
    adjs = [l.strip() for l in f.readlines()]

# save time, precompute and cache
emp_dist = precompute_employment_dist()


class Firm(Agent):
    config = {}

    def __init__(self, owner):
        self.owner = owner
        self.owner._state['firm_owner'] = True
        self.owner.firm = self
        self.desired_supply = 1

        # initialize
        self.workers = []
        self.revenue = 0
        self.costs = 0
        self.supply = 0
        self.n_sold = 0
        self.profit_margin = 1
        self.equipment = 0
        self.materials = 0

        # all states map to the same actions
        action_ids = [i for i in range(len(self.actions))]
        states_actions = {s: action_ids for s in range(5)}
        self.learner = QLearner(states_actions, self.reward, discount=0.5, explore=0.01, learning_rate=0.8)

        self.name = self.gen_name()

    def gen_name(self):
        return ''

    @property
    def id(self):
        return self.owner.id

    @property
    def public(self):
        return type(self.owner).__name__ == 'Government'

    def change_owner(self, owner):
        self.owner._state['firm_owner'] = False
        self.owner.firm = None

        owner._state['firm_owner'] = True
        owner.firm = self
        self.owner = owner

    def pay(self, cost):
        self.cash -= cost
        self.costs += cost

    @property
    def cash(self):
        return self.owner._state['cash']

    @cash.setter
    def cash(self, value):
        self.owner._state['cash'] = value

    @property
    def profit(self):
        return self.revenue - self.costs

    def __repr__(self):
        return '{}\'s {}'.format(self.owner.name, type(self).__name__)

    @property
    def production_capacity(self):
        return math.floor(self.labor/self.config['labor_cost_per_good'])

    @property
    def worker_labor(self):
        return self.config['labor_per_worker'] * len(self.workers)

    @property
    def equipment_labor(self):
        return min(len(self.workers), self.equipment) * self.config['labor_per_equipment']

    @property
    def labor(self):
        return self.worker_labor + self.equipment_labor

    def _labor(self, equipment):
        return self.worker_labor + min(len(self.workers), equipment) * self.config['labor_per_equipment']

    def fire(self, worker):
        worker.employer = None
        worker.wage = 0
        self.workers.remove(worker)
        logger.info('person:{}'.format(json.dumps({
            'event': 'fired',
            'id': worker.id
        })))

    def hire(self, applicants, wage, world):
        hired = []
        while self.worker_change > 0 and applicants:
            # based on employment prob
            apps = []
            for a in applicants:
                ref = 'friend' if set(a.friends).intersection(self.workers) else 'ad_or_cold_call'
                p = offer_prob(world['year'], world['month'], a.sex, a.race, ref, precomputed_emp_dist=emp_dist)
                apps.append((a, p))
            apps_mass = sum(p for a, p in apps)
            apps = [(a, pr/apps_mass) for a, pr in apps]

            worker = random_choice(apps)
            if worker.employer is not None:
                worker.employer.fire(worker)
            worker.wage = wage
            worker.employer = self
            applicants.remove(worker)
            self.workers.append(worker)
            hired.append(worker)
            logger.info('person:{}'.format(json.dumps({
                'event': 'hired',
                'id': worker.id,
                'wage': wage
            })))
            self.worker_change -= 1

        # increase wage to attract more employees
        if self.worker_change > 0:
            wage += self.config['wage_increment'] * (1.1+self.owner.altruism)
        return hired, self.worker_change, wage

    def close(self):
        self.owner._state['firm_owner'] = False
        self.owner.firm = None
        for worker in self.workers:
            self.fire(worker)

    def produce(self, world):
        """produce the firm's product. the firm will produce the desired supply if possible,
        otherwise, they will produce as much as they can."""

        # limit desired supply to what can be produced given current capacity
        self.supply = max(1, min(self.desired_supply, self.production_capacity))

        # set desired price
        wages = sum(w.wage for w in self.workers)
        self.costs += wages
        self.costs += self.building.rent/30 # approximately spread out rent cost
        self.cash -= wages
        cost_per_unit = self.costs/self.supply
        self.price = max(0, cost_per_unit + self.profit_margin)

        return self.supply, self.price

    def sell(self, quantity):
        n_sold = min(self.supply, quantity)
        self.supply -= n_sold
        self.n_sold += n_sold
        self.revenue = self.price * n_sold
        self.cash += self.revenue

    @property
    def current_state(self):
        """represent as a discrete state"""
        if self.n_sold == 0:
            return 0
        elif self.n_sold > 0 and self.leftover > 0:
            return 1
        elif self.n_sold > 0 and self.leftover == 0 and self.profit <= 0:
            return 2
        elif self.n_sold > 0 and self.leftover == 0 and self.profit > 0 and self.profit - self.prev_profit < 0:
            return 3
        elif self.n_sold > 0 and self.leftover == 0 and self.profit > 0 and self.profit - self.prev_profit >= 0:
            return 4

    def reward(self, state):
        """the discrete states we map to are the reward values, so just return that"""
        return state

    @property
    def actions(self):
        """these actions are possible from any state"""
        return [
            {'supply': self.config['supply_increment']},
            {'supply': -self.config['supply_increment']},
            {'supply': self.config['supply_increment'], 'profit_margin': self.config['profit_increment']},
            {'supply': self.config['supply_increment'], 'profit_margin': -self.config['profit_increment']},
            {'supply': -self.config['supply_increment'], 'profit_margin': self.config['profit_increment']},
            {'supply': -self.config['supply_increment'], 'profit_margin': -self.config['profit_increment']}
        ]

    def assess_assets(self, required_labor, mean_wage, mean_equip_price):
        """identify desired mixture of productive assets, i.e. workers, equipment, and wage"""
        down_wage_pressure = (-self.owner.altruism+1.1) * -self.config['wage_increment']

        def objective(x):
            n_workers, wage, n_equipment = x
            return n_workers * wage + n_equipment * mean_equip_price

        def constraint(x):
            n_workers, wage, n_equipment = x
            equip_labor = min(n_workers * self.config['labor_per_equipment'], n_equipment * self.config['labor_per_equipment'])
            return n_workers * self.config['labor_per_worker'] + equip_labor - required_labor

        results = optimize.minimize(objective, (1,0,0), constraints=[
            {'type': 'ineq', 'fun': constraint},
            {'type': 'ineq', 'fun': lambda x: x[0]},
            {'type': 'ineq', 'fun': lambda x: x[1] - (mean_wage - down_wage_pressure)},
            {'type': 'ineq', 'fun': lambda x: x[2]}
        ], options={'maxiter':20})
        n_workers, wage, n_equipment = np.ceil(results.x).astype(np.int)
        return n_workers, wage, n_equipment

    def purchase_equipment(self, supplier):
        total_equipment_cost = (self.desired_equipment - self.equipment) * supplier.price

        if not total_equipment_cost:
            n_equipment = max(0, self.desired_equipment - self.equipment)
        else:
            equipment_budget = max(0, min(self.cash, total_equipment_cost))

            # how much equipment can be purchased
            n_equipment = math.floor(equipment_budget/supplier.price)

        to_purchase = min(supplier.supply, n_equipment)
        supplier.sell(to_purchase)
        self.equipment += to_purchase
        cost = to_purchase * supplier.price
        self.cash -= cost
        self.costs += cost
        return self.desired_equipment - self.equipment, to_purchase

    def set_production_target(self, world):
        """firm decides on how much supply they want to produce this step,
        and what they need to do to accomplish that"""

        # assess previous day's results
        self.prev_profit = self.profit
        self.leftover = self.supply

        # adjust production
        action = self.learner.choose_action(self.current_state)
        action = self.actions[action]
        self.desired_supply = max(1, self.desired_supply + action.get('supply', 0))
        self.profit_margin += action.get('profit_margin', 0)

        # supply expires every day
        self.supply = 0

        # unused materials expire every day
        self.materials = 0

        # resets every day
        self.n_sold = 0
        self.revenue = 0
        self.costs = 0

        # fire workers that are being paid too much
        for worker in self.workers:
            if worker.wage >= world['mean_wage'] + (self.config['extravagant_wage_range'] * (1.1+self.owner.altruism)):
                self.fire(worker)

        # figure out labor goal
        required_labor = self.desired_supply * self.config['labor_cost_per_good']
        n_workers, wage, n_equip = self.assess_assets(required_labor, world['mean_wage'], world['mean_equip_price'])

        # sometimes optimization function returns a huge negative value for
        # workers, need to look into that further
        if n_workers < 0:
            n_workers = 0

        self.worker_change = n_workers - len(self.workers)
        self.desired_equipment = self.equipment + max(0, n_equip - self.equipment)

        # fire workers if necessary
        while self.worker_change < 0:
            # weighted random choice by unemployment prob
            ws = []
            for w in self.workers:
                pu = emp_dist[world['year']][world['month'] - 1][w.race.name][w.sex.name]
                ws.append((w, pu['unemployed']))
            ws_mass = sum(p for w, p in ws)
            ws = [(w, p/ws_mass) for w, p in ws]
            worker = random_choice(ws)
            self.fire(worker)
            self.worker_change += 1

        # job vacancies
        return self.worker_change, wage


class ConsumerGoodFirm(Firm):
    @property
    def production_capacity(self):
        return math.floor(min(self.labor/self.config['labor_cost_per_good'], self.materials/self.config['material_cost_per_good']))

    def purchase_materials(self, supplier):
        # figure out how much can be produced given current labor,
        # assuming the firm buys all the equipment they need
        capacity_given_labor = math.floor(self._labor(self.desired_equipment)/self.config['labor_cost_per_good'])

        # adjust desired production based on labor capacity
        self.desired_supply = min(capacity_given_labor, self.desired_supply)

        # estimate material costs
        required_materials = self.config['material_cost_per_good'] * self.desired_supply
        total_material_cost = (required_materials - self.materials) * supplier.price

        if not total_material_cost:
            n_materials = max(0, required_materials - self.materials)
        else:
            material_budget = max(0, min(self.cash, total_material_cost))

            # how many materials can be purchased
            n_materials = math.floor(material_budget/supplier.price)

        to_purchase = min(supplier.supply, n_materials)
        supplier.sell(to_purchase)
        self.materials += to_purchase

        cost = to_purchase * supplier.price
        self.cash -= cost
        self.costs += cost

        # how many materials are still required
        return required_materials - self.materials, to_purchase

    def gen_name(self):
        pre = [
            'Fresh',
            'Whole',
            'Organic',
            'Natural'
        ]
        suf = [
            'Market',
            'Mart',
            'Grocery',
            'Supermarket',
            'Foods'
        ]
        parts = []
        if random.random() <= 0.3:
            parts.append(random.choice(pre))
        elif random.random() <= 0.3:
            parts.append("{}'s".format(self.owner.split(' ')[-1]))
        else:
            parts.append(random.choice(adjs))
        parts.append(random.choice(suf))
        return ' '.join(parts)


class CapitalEquipmentFirm(ConsumerGoodFirm):
    def gen_name(self):
        pre = [
            'International',
            'Global',
            'Enterprise',
            'Capital'
        ]
        cat = [
            'Electronics',
            'Hardware',
            'Heavy Machinery',
            'Technologies',
            'Engineering',
            'Robotics',
            'Industries',
            'Solutions',
            'Machines',
            'Manufacturing',
            'Equipment',
        ]
        suf = [
            'LLC',
            'Inc',
            'Corporation',
            'Associated'
        ]
        parts = []
        if random.random() <= 0.1:
            parts.append(random.choice(pre))
        elif random.random() <= 0.2:
            parts.append("{}'s".format(self.owner.split(' ')[-1]))
        else:
            parts.append(random.choice(adjs))
        parts.append(random.choice(cat))
        if random.random() <= 0.2:
            parts.append(random.choice(suf))
        return ' '.join(parts)


class Hospital(Firm):
    """one hospital worker = one hospital supply"""

    @property
    def production_capacity(self):
        return len(self.workers)

    def produce(self, world):
        self.supply = self.production_capacity

        # set desired price
        wages = sum(w.wage for w in self.workers)
        self.costs += wages
        self.costs += self.building.rent/30 # approximately spread out rent cost
        self.cash -= wages
        cost_per_unit = self.costs/self.supply if self.supply else 0
        self.price = max(0, cost_per_unit + self.profit_margin)

        return self.supply, self.price

    def gen_name(self):
        suf = [
            'Clinic',
            'Center',
            'Hospital',
            'Treatment Center'
        ]
        parts = []
        if random.random() <= 0.7:
            parts.append(self.owner.split(' ')[-1])
        else:
            parts.append(random.choice(adjs))
        parts.append(random.choice(suf))
        return ' '.join(parts)


class RawMaterialFirm(Firm):
    def gen_name(self):
        suf = [
            'Mining',
            'Farming',
            'Foresters',
            'Oil',
            'Energy',
            'Gas',
            'Electric',
            'Metals',
            'Fuels',
            'Lumber',
            'Steel',
            'Alloys',
            'Drilling',
            'Agriculture',
            'Fishers',
            'Extraction',
            'Resources'
        ]
        parts = []
        if random.random() <= 0.4:
            parts.append("{}'s".format(self.owner.split(' ')[-1]))
        else:
            parts.append(random.choice(adjs))
        parts.append(random.choice(suf))
        return ' '.join(parts)
