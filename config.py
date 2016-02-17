import math
import random
import operator
import scipy.stats as st
from agent import Action, Prereq
from datetime import datetime
from world.work import offer_prob, job


START_DATE = datetime(day=1, month=1, year=2005)
START_HOUR = 0
HOURS_IN_DAY = 24
INCOME_BRACKETS = [-20000, -10000, 0, 1000, 5000, 10000, 20000, 25000, 30000, 35000,
                   40000, 45000, 50000, 55000, 60000, 65000, 70000, 90000, 110000,
                   200000, 500000, 9999998, 9999999]
SICK_PROB = 1/365 # arbitrary, what should this be?

CONSTRAINTS = {
    'stress': [0., None],
    'fatigue': [0., 1.],
    'health': [0., 1.],
    'rent_fail': [0, None],
}

# utility functions
# note that infinities do not work well here;
# they make it harder to compare utilities
UTILITY_FUNCS = {
    'health': lambda x: -10000 if x <= 0 else math.sqrt(x) * 100,
    'stress': lambda x: -(2**x) if x > 1 else 0.5 * math.log(-x+1+1e12) + 0.1,
    'fatigue': lambda x: -(2**x) if x > 1 else 0.5 * math.log(-x+1+1e12) + 0.1,
    'cash': lambda x: -1*(x+1) if x <= 0 else 400/(1 + math.exp(-x/20000)) - (400/2), # sigmoid for x > 0, linear otherwise
    'employed': lambda x: 200*math.sqrt(x) if x > 0. else -100 # TODO ideally this utility is inferred by the agent from the fact that employment gives them access to cash in the long term
}

def hire_dist(state):
    # more employed friends, more likely to have a referral
    p_referral = st.beta.rvs(state['employed_friends'] + 1, 10)
    if random.random() < p_referral:
        referral = 'friend'
    else:
        referral = 'ad_or_cold_call'
    p = offer_prob(state['world.year'], state['world.month'], state['sex'], state['race'], referral)
    return [1-p, p]

def get_job(state):
    return job(state['world.year'], state['sex'], state['race'], state['education'])

def dist(dist_name, params, factor=1):
    d = getattr(st, dist_name)(*params)
    def f(state):
        return factor * d.rvs(), factor * d.mean()
    return f

def dyndist(dist_name, param_func, factor=1):
    d = getattr(st, dist_name)
    def f(state):
        dist = d(*param_func(state))
        return factor * dist.rvs(), factor * dist.mean()
    return f


ACTIONS = [
    Action('relax',
        prereqs={
            'cash': Prereq(operator.ge, 100)
        },
        outcomes=([
            {'stress': dist('beta', (2,10), -1), 'cash': dist('beta', (2,10), -100), 'world.time': 2},
            {'stress': dist('beta', (2,6), -1), 'world.time': 2},
            {'stress': dist('beta', (1,10)), 'world.time': 2},
        ], [0.8, 0.1, 0.1])),
    Action('work',
        prereqs={
            'employed': Prereq(operator.eq, 1),
            'world.time': (Prereq(operator.ge, 6) & Prereq(operator.le, 18))
        },
        outcomes=([
            {'stress': dist('beta', (1,10)), 'cash': dyndist('gamma', lambda s: (max(s['income']/365, 1e-10), 10)), 'fatigue': 0.5, 'world.time': 4},
            {'stress': dist('beta', (1,8)), 'cash': dyndist('gamma', lambda s: (max(s['income']/365, 1e-10), 10)), 'fatigue': 0.6, 'world.time': 4}
        ], [0.8, 0.2])),
    Action('sleep',
        prereqs={},
        outcomes=([
            {'stress': dist('beta', (5,4), -1), 'fatigue': -1, 'cash': 0, 'world.time': 6},
        ], [1.])),
    Action('look for work',
        prereqs={
            'employed': Prereq(operator.eq, 0)
        },
        outcomes=([
            {'stress': dist('beta', (2,4)), 'world.time': 4},
            {'stress': dist('beta', (2,4)), 'world.time': 4,
             'employed': 1, '~': get_job, 'income': 1000} # for the purposes of planning, put in an exact income. the "~" function will compute the agent's actual income.
        ], hire_dist)),

    Action('visit doctor',
           prereqs={
               'cash': Prereq(operator.ge, 100)
           },
           outcomes=([
               {'health': 1., 'world.time': 2, 'cash': -100}
           ], [1.])),

    # TODO ideally we have some flexible-time thing happening
    # we need some action that takes only 1hr to fill in gaps
    Action('veg out',
           prereqs={},
           outcomes=([
               {'world.time': 1, 'stress': -0.05, 'fatigue': -0.05}
           ], [1.]))
]
