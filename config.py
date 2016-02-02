import math
import operator
import scipy.stats as st
from agent import Action, Prereq
from datetime import datetime


START_DATE = datetime(day=1, month=1, year=2005)
START_HOUR = 0
HOURS_IN_DAY = 24
INCOME_BRACKETS = [-20000, -10000, 0, 1000, 5000, 10000, 20000, 25000, 30000, 35000,
                   40000, 45000, 50000, 55000, 60000, 65000, 70000, 90000, 110000,
                   200000, 500000, 9999998, 9999999]
SICK_PROB = 1/365 # arbitrary, what should this be?

# utility functions
# note that infinities do not work well here;
# they make it harder to compare utilities
UTILITY_FUNCS = {
    'stress': lambda x: -(2**x) if x > 1 else 0.5 * math.log(-x+1+1e12) + 0.1,
    'fatigue': lambda x: -(2**x) if x > 1 else 0.5 * math.log(-x+1+1e12) + 0.1,
    'cash': lambda x: -1*(x+1) if x <= 0 else 10000/(1 + math.exp(-x)) - (10000/2), # sigmoid for x > 0, linear otherwise
    'employed': lambda x: 10000 if x == 1. else -10000 # TODO ideally this utility is inferred by the agent from the fact that employment gives them access to cash in the long term
}

ACTIONS = [
    Action('relax',
        prereqs={
        'cash': Prereq(operator.ge, 100)
        },
        outcomes=([
        {'stress': lambda s: -1 * st.beta.rvs(2,10), 'cash': lambda s: -100 * st.beta.rvs(2,10), 'world.time': 2},
        {'stress': lambda s: -1 * st.beta.rvs(2,6), 'world.time': 2},
        {'stress': lambda s: st.beta.rvs(1,10), 'world.time': 2},
        ], [0.8, 0.1, 0.1])),
    Action('work',
        prereqs={
        'employed': Prereq(operator.eq, 1),
        'world.time': (Prereq(operator.ge, 6) & Prereq(operator.le, 18))
        },
        outcomes=([
        {'stress': lambda s: st.beta.rvs(1,10), 'cash': 100, 'fatigue': 0.5, 'world.time': 4},
        {'stress': lambda s: st.beta.rvs(1,8), 'cash': 100, 'fatigue': 0.6, 'world.time': 4}
        ], [0.8, 0.2])),
    Action('sleep',
        prereqs={},
        outcomes=([
        {'stress': lambda s: -1 * st.beta.rvs(2,6), 'fatigue': -1, 'cash': 0, 'world.time': 6},
        ], [1.])),
    Action('look for work',
        prereqs={
        'employed': Prereq(operator.eq, 0)
        },
        outcomes=([
        {'stress': 0.5, 'world.time': 4},
        {'stress': 0.5, 'world.time': 4, 'employed': 1} # TODO replace with agent-specific prob
        ], [0.8, 0.2]))
]
