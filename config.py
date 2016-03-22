import random
import scipy.stats as st
from world.work import offer_prob, job


CONSTRAINTS = {
    'stress': [0., None],
    'health': [0., 1.],
    'rent_fail': [0, None],
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
