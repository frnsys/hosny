import math
import random
import logging
import numpy as np
from scipy import optimize
from cess import Agent
from cess.agent.learn import QLearner

logger = logging.getLogger('simulation.firms')

LABOR_COST_PER_GOOD = 2
MATERIAL_COST_PER_GOOD = 2
LABOR_PER_WORKER = 20
LABOR_PER_EQUIPMENT = 1
SUPPLY_INCREMENT = 1
PROFIT_INCREMENT = 1
WAGE_INCREMENT = 1
EXTRAVAGANT_WAGE_RANGE = 10
START_PROFIT_MARGIN = 1
RESIDENCE_SIZE_LIMIT = 100


class Firm(Agent):
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
        self.profit_margin = START_PROFIT_MARGIN
        self.equipment = 0
        self.materials = 0

        # all states map to the same actions
        action_ids = [i for i in range(len(self.actions))]
        states_actions = {s: action_ids for s in range(5)}
        self.learner = QLearner(states_actions, self.reward, discount=0.5, explore=0.01, learning_rate=0.5)

    @property
    def id(self):
        return self.owner.id

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
        return math.floor(self.labor/LABOR_COST_PER_GOOD)

    @property
    def worker_labor(self):
        return LABOR_PER_WORKER * len(self.workers)

    @property
    def equipment_labor(self):
        return min(len(self.workers), self.equipment) * LABOR_PER_EQUIPMENT

    @property
    def labor(self):
        return self.worker_labor + self.equipment_labor

    def _labor(self, equipment):
        return self.worker_labor + min(len(self.workers), equipment) * LABOR_PER_EQUIPMENT

    def fire(self, worker):
        worker.employer = None
        worker.wage = 0
        self.workers.remove(worker)

    def hire(self, applicants, wage):
        hired = []
        while self.worker_change > 0 and applicants:
            # TODO choose based on employment prob
            worker = random.choice(applicants)
            if worker.employer is not None:
                # logger.info('{} is leaving their old job at {}'.format(worker, worker.employer))
                worker.employer.fire(worker)
            worker.wage = wage
            worker.employer = self
            applicants.remove(worker)
            self.workers.append(worker)
            hired.append(worker)
            # logger.info('{} hired {} at wage {}'.format(self, worker, wage))
            self.worker_change -= 1

        # increase wage to attract more employees
        if self.worker_change > 0:
            wage += WAGE_INCREMENT * (1.1+self.owner.altruism)
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
        self.cash -= wages
        cost_per_unit = self.costs/self.supply
        self.price = max(0, cost_per_unit + self.profit_margin)

        # logger.info('{} produced {} at {}'.format(self, self.supply, self.price))
        return self.supply, self.price

    def sell(self, quantity):
        # logger.info('{} sold {} for {}'.format(self, quantity, self.price))
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
            {'supply': SUPPLY_INCREMENT},
            {'supply': -SUPPLY_INCREMENT},
            {'supply': SUPPLY_INCREMENT, 'profit_margin': PROFIT_INCREMENT},
            {'supply': SUPPLY_INCREMENT, 'profit_margin': -PROFIT_INCREMENT},
            {'supply': -SUPPLY_INCREMENT, 'profit_margin': PROFIT_INCREMENT},
            {'supply': -SUPPLY_INCREMENT, 'profit_margin': -PROFIT_INCREMENT}
        ]

    def assess_assets(self, required_labor, mean_wage, mean_equip_price):
        """identify desired mixture of productive assets, i.e. workers, equipment, and wage"""
        down_wage_pressure = (-self.owner.altruism+1.1) * -WAGE_INCREMENT

        def objective(x):
            n_workers, wage, n_equipment = x
            return n_workers * wage + n_equipment * mean_equip_price

        def constraint(x):
            n_workers, wage, n_equipment = x
            equip_labor = min(n_workers * LABOR_PER_EQUIPMENT, n_equipment * LABOR_PER_EQUIPMENT)
            return n_workers * LABOR_PER_WORKER + equip_labor - required_labor

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
            n_equipment = self.desired_equipment - self.equipment
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

        # logger.info('{}: {} profit, {} revenue, {} costs, {} cash'.format(self, self.profit, self.revenue, self.costs, self.cash))

        # adjust production
        action = self.learner.choose_action(self.current_state)
        action = self.actions[action]
        self.desired_supply = max(1, self.desired_supply + action.get('supply', 0))
        self.profit_margin += action.get('profit_margin', 0)

        # logger.info('{} desired supply {}'.format(self, self.desired_supply))

        # supply expires every day
        self.supply = 0

        # unused materials expire every day
        self.materials = 0

        # resets every day
        self.n_sold = 0
        self.revenue = 0
        self.costs = 0

        # figure out labor goal
        required_labor = self.desired_supply * LABOR_COST_PER_GOOD
        n_workers, wage, n_equip = self.assess_assets(required_labor, world['mean_wage'], world['mean_equip_price'])

        # fire workers that are being paid too much
        for worker in self.workers:
            if worker.wage >= world['mean_wage'] + (EXTRAVAGANT_WAGE_RANGE * (1.1+self.owner.altruism)):
                # logger.info('{} fired for being paid too much'.format(worker.id))
                self.fire(worker)

        self.worker_change = n_workers - len(self.workers)
        self.desired_equipment = self.equipment + max(0, n_equip - self.equipment)

        # fire workers if necessary
        while self.worker_change < 0:
            # TODO do weighted random choice by unemployment prob
            worker = random.choice(self.workers)
            # logger.info('{} fired because too many workers'.format(worker.id))
            self.fire(worker)
            self.worker_change += 1

        # job vacancies
        return self.worker_change, wage


class ConsumerGoodFirm(Firm):
    @property
    def production_capacity(self):
        return math.floor(min(self.labor/LABOR_COST_PER_GOOD, self.materials/MATERIAL_COST_PER_GOOD))

    def purchase_materials(self, supplier):
        # figure out how much can be produced given current labor,
        # assuming the firm buys all the equipment they need
        capacity_given_labor = math.floor(self._labor(self.desired_equipment)/LABOR_COST_PER_GOOD)

        # adjust desired production based on labor capacity
        self.desired_supply = min(capacity_given_labor, self.desired_supply)

        # estimate material costs
        required_materials = MATERIAL_COST_PER_GOOD * self.desired_supply
        total_material_cost = (required_materials - self.materials) * supplier.price

        if not total_material_cost:
            n_materials = required_materials - self.materials
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


class CapitalEquipmentFirm(ConsumerGoodFirm):
    pass


class Hospital(Firm):
    pass


class RawMaterialFirm(Firm):
    pass


class Residence(Firm):
    """similar to a regular firm, but has a supply fixed upon creation"""
    pass
