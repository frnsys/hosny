import math
import json
import random
import logging
import asyncio
import numpy as np
from datetime import datetime
from cess import Agent
from world import work
from .names import generate_name
from .generate import generate
from .attribs import Employed, Sex, Race, Education
from world.work import offer_prob
from cess.util import random_choice


logger = logging.getLogger('simulation.people')

# precompute and cache to save a lot of time
emp_dist = work.precompute_employment_dist()


class Person(Agent):
    base_min_consumption = 1
    wage_under_market_multiplier = 2
    min_business_capital = 50000 # initial required capital, plus whatever rent and an employee costs

    @classmethod
    def generate(cls, year, given=None, **kwargs):
        """generate a random person"""
        attribs = generate(year, given)
        attribs.pop('year', None)
        attribs.update(kwargs)
        return cls(**attribs)

    @property
    def quality_of_life(self):
        if hasattr(self, 'household'):
            return self.household.quality_of_life
        return None

    def purchasing_utility(self, utility, price):
        """`utility` is abstract; it can be "quality" for instance"""
        if not price:
            return utility**2
        return (utility**2)/(price * math.sqrt(1.1 + self.frugality))

    def health_utility(self, health):
        return -10000 if health <= 0 else math.sqrt(health) * 100

    def health_change_utility(self, change):
        return self.health_utility(self._state['health'] + change) - self.health_utility(self._state['health'])

    def cash_utility(self, cash):
        u = cash-1 if cash <= 0 else 400/(1 + math.exp(-cash/20000)) - (400/2) # sigmoid for cash > 0, linear otherwise
        return u * math.sqrt(1.1 + self.frugality)

    def cash_change_utility(self, change):
        return self.cash_utility(self._state['cash'] + change) - self.cash_utility(self._state['cash'])

    """an individual in the city"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        if 'name' not in kwargs:
            self.name = generate_name(self.sex, self.race)

        self.diary = {
            'days_unemployed': 0,
            'days_employed': 0
        }

        # the world initializes this
        self.friends = []

        self.sex = Sex(self.sex)
        self.race = Race(self.race)
        self.education = Education(self.education)

        # TODO these are being set manually
        self.altruism = 0
        self.frugality = 0
        self.wage = 0
        self.wage_minimum = 0
        self.employer = None
        self.firm = None
        self.min_consumption = self.base_min_consumption * (2 - self.frugality)

        # for associating websocket clients with a person
        self.sid = None

        super().__init__(
            state={
                'health': 1.,
                'stress': 0.5,
                'sick': False,

                # starting wealth
                'cash': 2*(self.wage_income + self.business_income + self.investment_income),

                'employed': self.employed,
                'wage_income': self.wage_income,
                'business_income': self.business_income,
                'investment_income': self.investment_income,

                # this will eventually be set by the dynamics of the world
                'welfare_income': self.welfare_income,

                'rent_fail': 0,
                'sex': self.sex,
                'race': self.race,
                'age': int(self.age),
                'education': self.education,
                'firm_owner': self.business_income > 0,

                # attribs
                'altruism': 0,      # negative: greedy
                'frugality': 0,     # negative: decadent/wasteful
                'myopism': 0,       # negative: better at long-term thinking
                'sociability': 0    # negative: introverted
            },
            constraints={
                'health': [0., 1.]
            })

    @asyncio.coroutine
    def step(self, world):
        """one time-step"""
        if self.state['employed'] == Employed.employed:
            self.diary['days_employed'] += 1

            f = self.fire_prob(world)
            if random.random() < f:
                self._state['employed'] = Employed.unemployed
                self.twoot('ah shit I got fired!', world)
        else:
            self.diary['days_unemployed'] += 1

            c = world['contact_rate']
            for friend in self.friends:
                employed = yield from friend['employed']
                if employed == Employed.employed and random.random() <= c:
                    p = self.hire_prob(world, 'friend')
                    if random.random() <= p:
                        self.twoot('got a job from my friend :)', world)
                        self._state['employed'] == Employed.employed
                        break

            # still don't have a job, cold call
            if self.state['employed'] != Employed.employed:
                p = self.hire_prob(world, 'ad_or_cold_call')
                if random.random() <= p:
                    self.twoot('got a job from a cold call!', world)
                    self._state['employed'] == Employed.employed

    def as_json(self):
        obj = self.state.copy()
        obj['friends'] = [friend.id for friend in self.friends]

        attrs = ['id', 'name',
                 'puma', 'industry',
                 'occupation', 'industry_code',
                 'occupation_code', 'neighborhood',
                 'rent', 'quality_of_life']
        for attr in attrs:
            obj[attr] = getattr(self, attr)

        # coerce numpy datatypes
        for k, v in obj.items():
            if isinstance(v, np.integer):
                obj[k] = int(v)
        return obj

    def __repr__(self):
        return self.name

    def hire_prob(self, world, referral):
        """referral can either be 'friend' or 'ad_or_cold_call'"""
        return offer_prob(world['year'], world['month'], self.state['sex'], self.state['race'], referral)

    def fire_prob(self, world):
        employment_dist = emp_dist[world['year']][world['month'] - 1][self.race.name][self.sex.name]
        p_unemployed = employment_dist['unemployed']/365 # kind of arbitrary denominator, what should this be?
        return p_unemployed

    def twoot(self, message, world):
        data = {
            'id': self.id,
            'name': self.name,
            'msg': message,
            'date': datetime.strptime(
                '{}/{}'.format(
                    world['month'],
                    world['year']),
                '%m/%Y').isoformat()
        }
        logger.info('twooter:{}'.format(json.dumps(data)))

    def seeking_job(self, world):
        if self._state['firm_owner']:
            return False
        if world['mean_consumer_good_price'] * self.min_consumption > self.wage:
            self.wage_minimum = world['mean_consumer_good_price'] * self.min_consumption
            return True
        elif world['mean_wage'] > self.wage * self.wage_under_market_multiplier:
            self.wage_minimum = self.wage * self.wage_under_market_multiplier
            return True
        return False

    def start_business(self, world, buildings):
        # can only have one business
        if self._state['firm_owner']:
            return False, None, None

        # must be able to find a place with affordable rent
        buildings = [b for b in buildings if b.available_space]
        if not buildings:
            return False, None, None

        denom = sum(1/b.rent for b in buildings)
        building = random_choice([(b, 1/(b.rent*denom)) for b in buildings])

        # must be able to hire at least one employee
        min_cost = self.min_business_capital + building.rent + world['mean_wage']

        if self._state['cash'] < min_cost:
            return False, None, None

        industries = ['equip', 'material', 'consumer_good', 'healthcare']
        total_mean_profit = sum(world['mean_{}_profit'.format(name)] for name in industries)
        industry_dist = [(name, world['mean_{}_profit'.format(name)]/total_mean_profit) for name in industries]
        industry = random_choice(industry_dist)

        # choose an industry (based on highest EWMA profit)
        self.twoot('i\'m starting a BUSINESS in {}!'.format(industry), world)

        logger.info('person:{}'.format(json.dumps({
            'event': 'started_firm',
            'id': self.id
        })))
        return True, industry, building
