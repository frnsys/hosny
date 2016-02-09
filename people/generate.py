"""
generates "plausible" residents using a
probabilistic graphical model (a bayes' net)
based on PUMS data
"""

import json
import random
import pandas as pd
import config
from . import attribs
from enum import Enum
from models.bnet import BNet
from world import rent


world_data = json.load(open('data/world/nyc.json', 'r'))
occupations = json.load(open('data/people/occupations.json', 'r'))
industries = json.load(open('data/people/industries.json', 'r'))
puma_to_neighborhoods = {int(k): v for k, v in world_data['puma_to_neighborhoods'].items()}


class Var(Enum):
    age = 'AGE'
    sex = 'SEX'
    race = 'RACE'
    puma = 'PUMA'
    education = 'EDUC'
    income = 'INCTOT'
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
    (Var.income, Var.puma),

    (Var.education, Var.income),
    (Var.sex, Var.income),
    (Var.age, Var.income),
    (Var.race, Var.income),
    (Var.employed, Var.income),
    (Var.occupation, Var.income),
    (Var.industry, Var.income),

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
    (Var.year, Var.income),
]

df = pd.read_csv('data/people/gen/pums_nyc.csv')
bins = {
    #Var.income: np.linspace(df.INCTOT.min(), df.INCTOT.max(), 10)
    Var.income: config.INCOME_BRACKETS
}
pgm = BNet(nodes, edges, df, bins, precompute=True)


def generate(year, given=None):
    """generates a single person"""
    given = given or {}
    given = {Var[k]: v for k, v in given.items()}
    given[Var.year] = year

    sample = pgm.sample(sampled=given)

    # 9999999 means N/A
    # https://usa.ipums.org/usa-action/variables/INCTOT#codes_section
    income_bracket = sample[Var.income]
    if income_bracket == '(9999998, 9999999]':
        sample[Var.income] = 0
    else:
        lbound, ubound = income_bracket[1:-1].split(',')
        sample[Var.income] = random.randint(int(lbound), int(ubound))

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

    sample['income_bracket'] = income_bracket

    # grab a neighborhood
    sample['neighborhood'] = random.choice(puma_to_neighborhoods[sample['puma']])

    sample['rent'] = rent.sample_rent(year, sample['puma'])

    sample['occupation_code'] = sample['occupation']
    sample['occupation'] = random.choice(occupations[str(sample['occupation_code'])])

    sample['industry_code'] = sample['industry']
    sample['industry'] = industries[str(sample['industry_code'])]

    return sample
