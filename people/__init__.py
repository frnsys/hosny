import json
import config
import random
import logging
import asyncio
from cess import Agent
from world import work
from .names import generate_name
from .generate import generate
from .attribs import Employed, Sex, Race, Education
from world.work import offer_prob

logger = logging.getLogger('simulation.people')


# precompute and cache to save a lot of time
emp_dist = work.precompute_employment_dist()


# assuming 1 adult. ofc these expenses will vary a lot depending on other
# factors like neighborhood, but we could not find data that granular
annual_expenses = sum(json.load(open('data/world/annual_expenses.json', 'r'))['1 adult'].values())




class Person(Agent):
    @classmethod
    def generate(cls, year, given=None, **kwargs):
        """generate a random person"""
        attribs = generate(year, given)
        attribs.pop('year', None)
        attribs.update(kwargs)
        return cls(**attribs)

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

        super().__init__(
            state={
                'health': 1.,
                'stress': 0.5,
                'cash': 1000,
                'employed': self.employed,
                'wage_income': self.wage_income,
                'business_income': self.business_income,
                'investment_income': self.investment_income,
                'retirement_income': self.retirement_income,
                'welfare_income': self.welfare_income,
                'rent_fail': 0,
                'sex': self.sex,
                'race': self.race,
                'age': int(self.age),
                'education': self.education,

                # attribs
                'altruism': 0,      # negative: greedy
                'frugality': 0,     # negative: decadent/wasteful
                'myopism': 0,       # negative: better at long-term thinking
                'sociability': 0    # negative: introverted
            },
            actions=config.ACTIONS,
            goals=[],
            utility_funcs=config.UTILITY_FUNCS,
            constraints=config.CONSTRAINTS)

    @asyncio.coroutine
    def step(self, world):
        """one time-step"""
        if self.state['employed'] == Employed.employed:
            self.diary['days_employed'] += 1

            f = self.fire_prob(world)
            if random.random() < f:
                self._state['employed'] = Employed.unemployed
                self.twoot('ah shit I got fired!')
        else:
            self.diary['days_unemployed'] += 1

            c = world['contact_rate']
            for friend in self.friends:
                employed = yield from friend['employed']
                if employed == Employed.employed and random.random() <= c:
                    p = self.hire_prob(world, 'friend')
                    if random.random() <= p:
                        self.twoot('got a job from my friend :)')
                        self._state['employed'] == Employed.employed
                        break

            # still don't have a job, cold call
            if self.state['employed'] != Employed.employed:
                p = self.hire_prob(world, 'ad_or_cold_call')
                if random.random() <= p:
                    self.twoot('got a job from a cold call!')
                    self._state['employed'] == Employed.employed

    def as_json(self):
        obj = self.state.copy()
        obj['friends'] = [friend.id for friend in self.friends]

        attrs = ['id', 'name',
                 'puma', 'industry',
                 'occupation', 'industry_code',
                 'occupation_code', 'neighborhood',
                 'rent']
        for attr in attrs:
            obj[attr] = getattr(self, attr)
        return obj

    def __repr__(self):
        return self.name

    def history(self):
        self.state['n_friends'] = len(self.friends)
        return self.name, self.state, self.diary

    def hire_prob(self, world, referral):
        """referral can either be 'friend' or 'ad_or_cold_call'"""
        return offer_prob(world['year'], world['month'], self.state['sex'], self.state['race'], referral)

    def fire_prob(self, world):
        employment_dist = emp_dist[world['year']][world['month'] - 1][self.race.name][self.sex.name]
        p_unemployed = employment_dist['unemployed']/365 # kind of arbitrary denominator, what should this be?
        return p_unemployed

    def twoot(self, message):
        data = {
            'id': self.id,
            'name': self.name,
            'msg': message
        }
        logger.info('twooter:{}'.format(json.dumps(data)))
