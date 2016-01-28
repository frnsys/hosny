"""
computes a probability distribution over first names given sex,
based on 1990 census data.

    Female/male first names from the Census 1990
    http://deron.meranda.us/data/

"""

import json
import pandas as pd

name_given_sex = {
    'male': {},
    'female': {}
}

for sex in name_given_sex.keys():
    fname = 'src/census-dist-{}-first.txt'.format(sex)

    # only need columns 0 and 1 (names and percent in population)
    df = pd.read_csv(fname,
                     header=None,
                     delim_whitespace=True,
                     usecols=[0,1],
                     index_col=0,
                     names=['name', 'prob'])

    # normalize to a distribution
    df.prob /= df.prob.sum()
    name_given_sex[sex] = df.prob.to_dict()

with open('gen/name_given_sex.json', 'w') as f:
    json.dump(name_given_sex, f)