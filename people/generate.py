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


world_data = json.load(open('data/world/nyc.json', 'r'))
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

    (Var.education, Var.employed),
    (Var.sex, Var.employed),
    (Var.age, Var.employed),
    (Var.race, Var.employed),

    (Var.employed, Var.occupation),
    (Var.education, Var.occupation),
    (Var.sex, Var.occupation),
    (Var.age, Var.occupation),
    (Var.race, Var.occupation),
]

df = pd.read_csv('data/people/gen/pums_nyc.csv')
bins = {
    #Var.income: np.linspace(df.INCTOT.min(), df.INCTOT.max(), 10)
    Var.income: [-20000, -10000, 0, 10000, 20000, 30000, 50000, 70000, 90000, 110000, 200000, 500000, 9999998, 9999999]
}
pgm = BNet(nodes, edges, df, bins)


def generate():
    """generates a single person"""
    sample = pgm.sample()

    # 9999999 means N/A
    # https://usa.ipums.org/usa-action/variables/INCTOT#codes_section
    if sample[Var.income] == '(9999998, 9999999]':
        sample[Var.income] = None

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

    # grab a neighborhood
    sample['neighborhood'] = random.choice(puma_to_neighborhoods[sample['puma']])

    return sample
