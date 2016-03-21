import math
import json
import random
import config
import logging
from cess import Simulation
from cess.util import random_choice
from economy import Household, ConsumerGoodFirm, CapitalEquipmentFirm, RawMaterialFirm, Building
from dateutil.relativedelta import relativedelta

world_data = json.load(open('data/world/nyc.json', 'r'))

STARTING_WAGE = 5
MAX_ROUNDS = 10

logger = logging.getLogger('simulation.city')


def shuffle(l):
    random.shuffle(l)
    return l


def ewma(p_mean, val, alpha=0.8):
    """computes exponentially weighted moving mean"""
    return p_mean + (alpha * (val - p_mean))


class City(Simulation):
    def __init__(self, people, conf):
        super().__init__(people)

        self.buildings = [
            Building(conf['max_tenants'])
                     for _ in range(conf['n_buildings'])]

        # the world state
        self.date = config.START_DATE
        self.state = {
            'month': self.date.month,
            'year': self.date.year,
            'contact_rate': 0.4,
            'mean_wage': STARTING_WAGE,
            'available_space': len(self.buildings) * conf['max_tenants'],
            'mean_equip_price': 5, #TODO what should this be?
            'mean_consumer_good_price': 5, #TODO what should this be?

            # just initialize to some values
            'mean_equip_profit': 1,
            'mean_material_profit': 1,
            'mean_consumer_good_profit': 1,
        }

        self.people = people

        # TODO create "real" households
        self.households = [Household([p]) for p in people]

        self.firms = []
        self.consumer_good_firms = []
        self.raw_material_firms = []
        self.capital_equipment_firms = []

    def step(self):
        """one time step in the model (a day)"""
        super().step()
        self.date += relativedelta(days=1)
        self.state['month'] = self.date.month
        self.state['year'] = self.date.year

        # self.real_estate_market()

        # see if anyone want to start a business
        # only possible if there is space available to rent
        self.state['available_space'] = sum(b.available_space for b in self.buildings)
        n_tenants = sum(len(b.tenants) for b in self.buildings)
        mean_rent = sum(b.rent * len(b.tenants) for b in self.buildings)/n_tenants if n_tenants else 0
        self.ewma_stat('mean_rent', mean_rent, graph=True)
        if self.state['available_space']:
            for person in shuffle(self.people):
                yes, industry, building = person.start_business(self.state, self.buildings)
                if yes:
                    if industry == 'equip':
                        firm = CapitalEquipmentFirm(person)
                        self.capital_equipment_firms.append(firm)
                    elif industry == 'material':
                        firm = RawMaterialFirm(person)
                        self.raw_material_firms.append(firm)
                    elif industry == 'consumer_good':
                        firm = ConsumerGoodFirm(person)
                        self.consumer_good_firms.append(firm)
                    building.add_tenant(firm)
                    self.firms.append(firm)

        jobs = []
        for firm in shuffle(self.firms):
            n_vacancies, wage = firm.set_production_target(self.state)
            jobs.append((n_vacancies, wage, firm))

        self.labor_market(jobs)

        labor_force = [p for p in self.people if p.wage != 0]
        self.ewma_stat('mean_wage', sum(p.wage for p in labor_force)/len(labor_force), graph=True)

        for firm in self.raw_material_firms:
            firm.produce(self.state)

        sold, profits = self.raw_material_market()
        mean = sum(profits)/len(profits) if profits else 0
        self.ewma_stat('mean_material_profit', mean, graph=True)

        for firm in self.capital_equipment_firms:
            firm.produce(self.state)

        sold, profits = self.capital_equipment_market()
        mean = sum(profits)/len(profits) if profits else 0
        self.ewma_stat('mean_equip_profit', mean, graph=True)

        sell_prices = []
        for amt, price in sold:
            sell_prices += [price for _ in range(amt)]
        mean = sum(sell_prices)/len(sell_prices) if sell_prices else 0
        self.ewma_stat('mean_equip_price', mean, graph=True)

        for firm in self.consumer_good_firms:
            firm.produce(self.state)

        sold, profits = self.consumer_good_market()
        mean = sum(profits)/len(profits) if profits else 0
        self.ewma_stat('mean_consumer_good_profit', mean, graph=True)

        sell_prices = []
        for amt, price in sold:
            sell_prices += [price for _ in range(amt)]
        mean = sum(sell_prices)/len(sell_prices) if sell_prices else 0
        self.ewma_stat('mean_consumer_good_price', mean, graph=True)

        # TODO payment
        # TODO taxes
        # for person in self.people:
            # person['cash'] = (yield from person['cash']) + person.wage

        # TODO decide on hospitals
        # TODO healthcare profits
        # self.ewma_stat('mean_consumer_good_profit', sum(profits)/len(profits), graph=True)

        for firm in self.firms:
            # bankrupt
            if firm.cash < 0:
                # logger.info('{} is going bankrupt!'.format(firm))
                self.firms.remove(firm)
                # messy
                for firm_group in [self.consumer_good_firms, self.capital_equipment_firms, self.raw_material_firms]:
                    if firm in firm_group:
                        firm_group.remove(firm)
                for building in self.buildings:
                    if firm in building.tenants:
                        building.remove_tenant(firm)
                        break
                firm.owner._state['firm_owner'] = False

        # TODO government decisions

    def _log(self, chan, data):
        """format a message for the logger"""
        logger.info('{}:{}'.format(chan, json.dumps(data)))

    def labor_market(self, jobs):
        job_seekers = [p for p in self.people if p.seeking_job(self.state)]
        applicants = {f: [] for _, __, f in jobs}

        # iterate until there are no more job seekers or no more jobs
        while job_seekers and jobs:
            # job seekers apply to jobs which satisfy their wage criteria
            # TODO should they apply to anything if nothing satifies their
            # criteria?
            for p in shuffle(job_seekers):
                for job in jobs:
                    n_vacancies, wage, firm = job
                    if wage >= p.wage_minimum:
                        applicants[firm].append(p)

            # firms select from their applicants
            _jobs = []
            for job in jobs:
                # filter down to valid applicants
                apps = [a for a in applicants[firm] if a in job_seekers]
                n_vacancies, wage, firm = job
                hired, n_vacancies, wage = firm.hire(apps, wage)

                # remove hired people from the job seeker pool
                for p in hired:
                    job_seekers.remove(p)

                if not job_seekers:
                    break

                # if vacancies remain, post the new jobs with the new wage
                if n_vacancies:
                    _jobs.append((n_vacancies, wage, firm))
            jobs = _jobs

    def raw_material_market(self):
        sold = []
        firm_dist = self.firm_distribution(self.raw_material_firms)

        firms = self.consumer_good_firms + self.capital_equipment_firms
        rounds = 0
        while firms and firm_dist and rounds < MAX_ROUNDS:
            for firm in shuffle(firms):
                supplier = random_choice(firm_dist)
                required, purchased = firm.purchase_materials(supplier)
                sold.append((purchased, supplier.price))
                if required == 0:
                    firms.remove(firm)

                # if supplier sold out, update firm distribution
                if supplier.supply == 0:
                    firm_dist = self.firm_distribution(self.raw_material_firms)

                if not firm_dist:
                    break
            rounds += 1
        profits = [f.revenue - f.costs for f in self.raw_material_firms]
        return sold, profits

    def firm_distribution(self, firms):
        """computes a probability distribution over firms based on their prices.
        the lower the price, the more likely they are to be chosen"""
        firms = [f for f in firms if f.supply > 0]
        probs = [math.exp(-math.log(f.price)) for f in firms]
        mass = sum(probs)
        return [(f, p/mass) for f, p in zip(firms, probs)]

    def capital_equipment_market(self):
        sold = []
        firm_dist = self.firm_distribution(self.capital_equipment_firms)

        firms = self.consumer_good_firms + self.raw_material_firms
        rounds = 0
        while firms and firm_dist and rounds < MAX_ROUNDS:
            for firm in shuffle(firms):
                supplier = random_choice(firm_dist)
                required, purchased = firm.purchase_equipment(supplier)
                sold.append((purchased, supplier.price))
                if required == 0:
                    firms.remove(firm)

                # if supplier sold out, update firm distribution
                if supplier.supply == 0:
                    firm_dist = self.firm_distribution(self.capital_equipment_firms)

                if not firm_dist:
                    break
            rounds += 1
        profits = [f.revenue - f.costs for f in self.capital_equipment_firms]
        return sold, profits

    def consumer_good_market(self):
        firm_dist = self.firm_distribution(self.consumer_good_firms)

        sold = []
        households = [h for h in self.households]
        rounds = 0
        while households and firm_dist and rounds < MAX_ROUNDS:
            for household in shuffle(households):
                supplier = random_choice(firm_dist)
                desired, purchased = household.purchase_goods(supplier)
                sold.append((purchased, supplier.price))

                if desired == 0:
                    households.remove(household)

                # if supplier sold out, update firm distribution
                if supplier.supply == 0:
                    firm_dist = self.firm_distribution(self.consumer_good_firms)

                if not firm_dist:
                    break
            rounds += 1

        profits = [f.revenue - f.costs for f in self.consumer_good_firms]
        return sold, profits

    def ewma_stat(self, name, update, graph=False, start_value=0):
        """updates an EWMA for a state, optionally send a socket message
        to graph the result"""
        self.state[name] = ewma(self.state.get(name, start_value), update)
        if graph:
            data = json.dumps({'graph':name,'data':{'time':self.date.isoformat(),'value': self.state[name]}})
            logger.info('graph:{}'.format(data))
