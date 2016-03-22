import math
import json
import random
import logging
from datetime import datetime
from cess import Simulation
from cess.util import random_choice
from people import Person
from economy import Household, Firm, ConsumerGoodFirm, CapitalEquipmentFirm, RawMaterialFirm, Hospital, Building, Government
from dateutil.relativedelta import relativedelta

world_data = json.load(open('data/world/nyc.json', 'r'))

default_conf = {
    'starting_wage': 5,
    'max_tenants': 10,
    'n_buildings': 16,
    'patient_zero_prob': 0.01,
    'contact_rate': 0.1,
    'transmission_rate': 0.1,
    'sickness_severity': 0.01,
    'tax_rate': 0.3,
    'tax_rate_increment': 0.1,
    'welfare_increment': 1,
    'welfare': 10,
    'consumer_good_utility': 1,
    'rent': 1000,
    'labor_cost_per_good': 2,
    'material_cost_per_good': 2,
    'labor_per_worker': 20,
    'labor_per_equipment': 1,
    'supply_increment': 1,
    'profit_increment': 1,
    'wage_increment': 1,
    'extravagant_wage_range': 10,
    'residence_size_limit': 100,
    'base_min_consumption': 1,
    'wage_under_market_multiplier': 1,
    'min_business_capital': 50000
}

START_DATE = datetime(day=1, month=1, year=2005)
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

        config = default_conf.copy()
        config.update(conf)

        Firm.config = config
        Person.base_min_consumption = config['base_min_consumption']
        Person.wage_under_market_multiplier = config['wage_under_market_multiplier']
        Person.min_business_capital = config['min_business_capital']

        self.government = Government(config['tax_rate'], config['welfare'], config['tax_rate_increment'], config['welfare_increment'])

        self.buildings = [
            Building(config['max_tenants'], config['rent'])
                     for _ in range(config['n_buildings'])]

        # the world state
        self.date = START_DATE
        self.state = {
            'month': self.date.month,
            'year': self.date.year,

            # contagion model
            'patient_zero_prob': config['patient_zero_prob'],
            'contact_rate': config['contact_rate'],
            'transmission_rate': config['transmission_rate'],
            'sickness_severity': config['sickness_severity'],

            'mean_wage': config['starting_wage'],
            'available_space': len(self.buildings) * config['max_tenants'],

            # just initialize to some values
            'mean_equip_price': 1,
            'mean_consumer_good_price': 1,
            'mean_equip_profit': 1,
            'mean_material_profit': 1,
            'mean_consumer_good_profit': 1,
            'mean_healthcare_profit': 1,
        }

        self.people = people

        # TODO create "real" households
        self.households = [Household([p], config['consumer_good_utility']) for p in people]

        self.firms = []
        self.consumer_good_firms = []
        self.raw_material_firms = []
        self.capital_equipment_firms = []
        self.hospitals = []

        self.initialized = False

    def step(self):
        """one time step in the model (a day)"""
        super().step()

        prev_month = self.date.month

        self.date += relativedelta(days=1)
        self.state['month'] = self.date.month
        self.state['year'] = self.date.year

        if not self.initialized:
            # create initial firms
            for person in self.people:
                if person._state['firm_owner']:
                    industry = random.choice(['equip', 'material', 'consumer_good', 'healthcare'])
                    building = random.choice(self.buildings)
                    self.start_firm(person, industry, building)
            self.initialized = True

        # month change
        if prev_month != self.date.month:
            # pay rent
            for building in self.buildings:
                for tenant in building.tenants:
                    tenant.pay(building.rent)

        for household in self.households:
            household.step()

        n_deaths = self.contagion_model()
        self.stat('n_sick', len([p for p in self.people if p._state['sick']]))

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
                    self.start_firm(person, industry, building)

        jobs = []
        for firm in shuffle(self.firms):
            n_vacancies, wage = firm.set_production_target(self.state)
            jobs.append((n_vacancies, wage, firm))

        self.labor_market(jobs)

        labor_force = [p for p in self.people if p.wage != 0]
        mean_wage = sum(p.wage for p in labor_force)/len(labor_force) if labor_force else 0
        self.ewma_stat('mean_wage', mean_wage, graph=True)

        for firm in self.raw_material_firms:
            firm.produce(self.state)

        sold, profits = self.raw_material_market()
        mean = sum(profits)/len(profits) if profits else 0
        self.ewma_stat('mean_material_profit', mean, graph=True)

        sell_prices = []
        for amt, price in sold:
            sell_prices += [price for _ in range(amt)]
        mean = sum(sell_prices)/len(sell_prices) if sell_prices else 0
        self.ewma_stat('mean_material_price', mean, graph=True)

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

        for household in self.households:
            if not household.check_goods():
                pass
                # for p in household.people:
                    # self.dies(p)
                    # n_deaths += 1
        self.stat('n_deaths', n_deaths)
        self.stat('n_population', len(self.people))

        # taxes and wages
        for person in self.people:
            if person._state['firm_owner']:
                profit = max(person.firm.profit, 0)
                taxes = profit * self.government.tax_rate
                person.firm.cash -= taxes
            else:
                taxes = person.wage * self.government.tax_rate
                person._state['cash'] += (person.wage - taxes)
            self.government.cash += taxes

        for firm in self.hospitals:
            firm.produce(self.state)

        sold, profits = self.healthcare_market()
        mean = sum(profits)/len(profits) if profits else 0
        self.ewma_stat('mean_healthcare_profit', mean, graph=True)
        mean = sum(sold)/len(sold) if sold else 0
        self.ewma_stat('mean_healthcare_price', mean, graph=True)

        n_bankruptcies = 0
        for firm in self.firms:
            # bankrupt
            if firm.cash < 0:
                n_bankruptcies += 1
                self.close_firm(firm)

        self.stat('n_bankruptcies', n_bankruptcies)
        self.stat('n_firms', len(self.firms))

        mean_quality_of_life = sum(h.quality_of_life for h in self.households)/len(self.households) if self.households else 0
        self.ewma_stat('mean_quality_of_life', mean_quality_of_life, graph=True)

        mean_cash = sum(h.cash for h in self.households)/len(self.households) if self.households else 0
        self.ewma_stat('mean_cash', mean_cash, graph=True)

        self.government.adjust(self.households)
        self.stat('welfare', self.government.welfare)
        self.stat('tax_rate', self.government.tax_rate)

        for person in self.people:
            person._state['cash'] += self.government.welfare
            self.government.cash -= self.government.welfare

    def start_firm(self, person, industry, building):
        if industry == 'equip':
            firm = CapitalEquipmentFirm(person)
            self.capital_equipment_firms.append(firm)
        elif industry == 'material':
            firm = RawMaterialFirm(person)
            self.raw_material_firms.append(firm)
        elif industry == 'consumer_good':
            firm = ConsumerGoodFirm(person)
            self.consumer_good_firms.append(firm)
        elif industry == 'healthcare':
            firm = Hospital(person)
            self.hospitals.append(firm)
        building.add_tenant(firm)
        self.firms.append(firm)

    def close_firm(self, firm):
        self.firms.remove(firm)
        # messy
        for firm_group in [self.consumer_good_firms, self.capital_equipment_firms, self.raw_material_firms]:
            if firm in firm_group:
                firm_group.remove(firm)
        for building in self.buildings:
            if firm in building.tenants:
                building.remove_tenant(firm)
                break
        firm.close()

    def contagion_model(self):
        deaths = 0

        # if anyone is sick
        if any(p._state['sick'] for p in self.people):
            # run contagion/sickness model
            c = self.state['contact_rate']
            for person in self.people:
                if person._state['sick']:
                    # each sick person loses a little health
                    person._state['health'] -= self.state['sickness_severity']
                    if person._state['health'] <= 0:
                        self.dies(person)
                        deaths += 1
                    continue
                for friend in person.friends:
                    if random.random() <= c and random.random() <= self.state['transmission_rate']:
                        person.twoot('feeling sick...', self.state)
                        break
        # otherwise, see if a new sickness starts
        elif random.random() < self.state['patient_zero_prob']:
            patient_zero = random.choice(self.people)
            patient_zero._state['sick'] = True
            patient_zero.twoot('feeling sick...', self.state)

        return deaths

    def dies(self, person):
        if person._state['firm_owner']:
            self.close_firm(person.firm)
        elif person.employer is not None:
            person.employer.fire(person)
        self.people.remove(person)
        household = person.household
        household.people.remove(person)
        if not household.people:
            self.households.remove(household)
        logger.info('person:{}'.format(json.dumps({
            'event': 'died',
            'id': person.id
        })))

    def firm_distribution(self, firms):
        """computes a probability distribution over firms based on their prices.
        the lower the price, the more likely they are to be chosen"""
        firms = [f for f in firms if f.supply > 0]
        probs = [math.exp(-math.log(f.price)) if f.price > 0 else 1. for f in firms]
        mass = sum(probs)
        return [(f, p/mass) for f, p in zip(firms, probs)]

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
                n_vacancies, wage, firm = job
                apps = [a for a in applicants[firm] if a in job_seekers]
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

    def healthcare_market(self):
        sold = []
        hospitals = [h for h in self.hospitals]
        for person in shuffle(self.people):
            if person._state['health'] < 1.:
                affordable = [h for h in hospitals if h.price <= person._state['cash']]
                if not affordable:
                    continue
                utilities = [person.health_change_utility(1 - person._state['health']) + person.cash_change_utility(-h.price) for h in affordable]
                u_t = sum(utilities)
                choices = [(h, u/u_t) for h, u in zip(hospitals, utilities)]
                hospital = random_choice(choices)
                hospital.sell(1)
                person._state['cash'] -= hospital.price
                person._state['health'] = 1
                person._state['sick'] = False
                sold.append(hospital.price)
                if hospital.supply == 0:
                    hospitals.remove(hospital)
                if not hospitals:
                    break

        profits = [f.revenue - f.costs for f in self.hospitals]
        return sold, profits

    def ewma_stat(self, name, update, graph=False, start_value=0):
        """updates an EWMA for a state, optionally send a socket message
        to graph the result"""
        self.state[name] = ewma(self.state.get(name, start_value), update)
        if graph:
            data = json.dumps({'graph':name,'data':{'time':self.date.isoformat(),'value': self.state[name]}})
            logger.info('graph:{}'.format(data))

    def stat(self, name, value):
        """updates an EWMA for a state, optionally send a socket message
        to graph the result"""
        data = json.dumps({'graph':name,'data':{'time':self.date.isoformat(),'value': value}})
        logger.info('graph:{}'.format(data))

    def _log(self, chan, data):
        """format a message for the logger"""
        logger.info('{}:{}'.format(chan, json.dumps(data)))
