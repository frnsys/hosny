"""
a naive bayes approach to placing simulated individuals into
neighborhoods based on their attributes and aggregate neighborhood data
from the American Community Survey.

we are interested in p(N_k|x_1, ..., x_n),
where (x_1, ..., x_n) are the attributes (e.g. income, rent, etc).
we make the naive independence assumption which gives us:

    p(N_k|x_1, ..., x_n) \varpropto p(N) \prod_{i=1}^n p(x_i|N_k)

this is a strong assumption, but it simplifies things quite a bit
"""

import random


def p_n(populations):
    """computes p(N_k) (the prior).
    populations should be a dict:
    {neighborhood: population, ...}
    """
    probs = {}
    total_pop = sum(populations.values())
    for n, pop in populations.items():
        probs[n] = pop/total_pop
    return probs


def dist_for_person(person, neighborhoods):
    """computes distribution over neighborhoods
    given a person's attributes"""

    # compute prior
    probs = p_n(populations)

    # compute likelihood
    for neighborhood, attrs in neighborhoods.items():
        for attr, attr_vals in attrs.items():
            total_attr_pop = sum(attr_vals.values())
            p = attr_vals[person[attr]]/total_attr_pop
            probs[neighborhood] *= p

    # normalize
    total = sum(probs.values())
    for neighborhood in probs.keys():
        probs[neighborhood] /= total

    return probs


def random_choice(choices):
    """returns a random choice from a list
    of (choice, probability) pairs."""
    roll = random.random()

    # sort by probability
    choices = sorted(choices, key=lambda x:x[1])
    for choice, prob in choices:
        if roll <= prob:
            return choice




# example

neighborhoods = {
    'A': {
        'income': {
            'less than $10,000': 1000,
            '$10,000-$50,000': 2000,
            'greater than $50,000': 100
        },
        'rent': {
            'less than $1000': 2000,
            '$1000-$2000': 1080,
            'greater than $2000': 20
        }
    },
    'B': {
        'income': {
            'less than $10,000': 100,
            '$10,000-$50,000': 200,
            'greater than $50,000': 4000
        },
        'rent': {
            'less than $1000': 10,
            '$1000-$2000': 2000,
            'greater than $2000': 2290
        }
    }
}

populations = {
    'A': 3100,
    'B': 4300
}

person = {
    'income': 'greater than $50,000',
    'rent': '$1000-$2000'
}

probs = dist_for_person(person, neighborhoods)
print('distribution:', probs)
print('neighborhood:', random_choice(probs.items()))
