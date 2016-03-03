"""
generates "plausible" residents using a
probabilistic graphical model (a bayes' net)
based on PUMS data
"""

import json
import random
import pandas as pd
from . import attribs
from enum import Enum
from models.bnet import BNet
from world import rent
from world.work import income_brackets


with open('data/world/nyc.json', 'r') as f:
    world_data = json.load(f)

with open('data/people/occupations.json', 'r') as f:
    occupations = json.load(f)

with open('data/people/industries.json', 'r') as f:
    industries = json.load(f)

puma_to_neighborhoods = {int(k): v for k, v in world_data['puma_to_neighborhoods'].items()}


class Var(Enum):
    age = 'AGE'
    sex = 'SEX'
    race = 'RACE'
    puma = 'PUMA'
    education = 'EDUC'
    wage_income = 'INCWAGE'
    investment_income = 'INCINVST'
    welfare_income = 'INCWELFR'
    retirement_income = 'INCRETIR'
    business_income = 'INCBUS00'
    social_security_income = 'INCSS'
    employed = 'EMPSTAT'
    occupation = 'OCC2010'
    industry = 'IND'
    year = 'YEAR'

nodes = list(Var)
edges = [
    (Var.age, Var.education),
    (Var.sex, Var.education),
    (Var.race, Var.education),

    (Var.race, Var.puma),
    (Var.age, Var.puma),

    (Var.education, Var.employed),
    (Var.sex, Var.employed),
    (Var.age, Var.employed),
    (Var.race, Var.employed),

    (Var.sex, Var.industry),
    (Var.age, Var.industry),
    (Var.race, Var.industry),
    (Var.education, Var.industry),
    (Var.employed, Var.industry),

    (Var.industry, Var.occupation),
    (Var.employed, Var.occupation),
    (Var.education, Var.occupation),
    (Var.sex, Var.occupation),
    (Var.age, Var.occupation),
    (Var.race, Var.occupation),

    (Var.year, Var.employed),

    (Var.wage_income, Var.welfare_income),
    (Var.business_income, Var.wage_income),
    (Var.wage_income, Var.retirement_income),
    (Var.wage_income, Var.social_security_income),
]


income_vars = [
    Var.wage_income,
    Var.investment_income,
    Var.welfare_income,
    Var.retirement_income,
    Var.business_income,
    Var.social_security_income
]

for income_var in income_vars:
    edges += [(var, income_var) for var
              in [Var.education, Var.sex, Var.age, Var.race,
                 Var.employed, Var.occupation, Var.industry, Var.year]]
    edges.append((income_var, Var.puma))


df = pd.read_csv('data/people/gen/pums_nyc.csv')
bins = {income_var: income_brackets[income_var.value] for income_var in income_vars}
pgm = BNet(nodes, edges, df, bins, precompute=True)


def generate(year, given=None):
    """generates a single person"""
    given = given or {}
    given = {Var[k]: v for k, v in given.items()}
    given[Var.year] = year

    sample = pgm.sample(sampled=given)

    income_brackets = {}
    for income_var in income_vars:
        na_val = '{}]'.format(df[income_var.value].max())
        income_bracket = sample[income_var]
        if income_bracket.endswith(na_val)\
                or income_bracket.endswith('0]')\
                or income_bracket.startswith('(0'):
            sample[income_var] = 0
        else:
            lbound, ubound = income_bracket[1:-1].split(',')
            sample[income_var] = random.randint(int(float(lbound)), int(float(ubound)))

        income_brackets['{}_bracket'.format(income_var.name)] = income_bracket

    # convert to enums
    for var, enum in [
        (Var.sex, attribs.Sex),
        (Var.race, attribs.Race),
        (Var.education, attribs.Education),
        (Var.employed, attribs.Employed)
    ]:
        sample[var] = enum(sample[var])

    # rename keys
    sample = {k.name: v for k,v in sample.items()}

    # add in income brackets
    sample.update(income_brackets)

    # grab a neighborhood
    sample['neighborhood'] = random.choice(puma_to_neighborhoods[sample['puma']])

    sample['rent'] = rent.sample_rent(year, sample['puma'])

    sample['occupation_code'] = sample['occupation']
    sample['occupation'] = random.choice(occupations[str(sample['occupation_code'])])

    sample['industry_code'] = sample['industry']
    sample['industry'] = industries[str(sample['industry_code'])]

    return sample
