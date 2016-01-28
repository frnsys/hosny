"""
computes probability distributions over surnames given a race,
from 2000 census data of surnames present >=100 times.

    Frequently Occurring Surnames from the Census 2000
    http://www.census.gov/topics/population/genealogy/data/2000_surnames.html
    Surnames occurring >= 100 times in the 2000 census.
    details here: http://www2.census.gov/topics/genealogy/2000surnames/surnames.pdf

"""

import json
import pandas as pd

df = pd.read_csv('src/census_surnames_2000.csv')

races = ['white', 'black', 'api', 'aian', '2prace', 'hispanic']
surname_given_race = {race: {} for race in races}

# compute raw counts of names for races
for i, row in df.iterrows():
    name = row['name']

    # skip nan
    if isinstance(name, float):
        continue

    count = row['count']
    for race in races:
        # get the percent of people with this last name
        # who identify as this race
        col = 'pct{}'.format(race)
        pct = row[col]

        # suppressed for confidentiality, skip
        if pct == '(S)':
            continue

        count_for_race = count * float(pct)/100
        surname_given_race[race][name] = count_for_race

# normalize to a probability distribution
for race, names in surname_given_race.items():
    total = sum(names.values())
    for name, count in names.items():
        names[name] /= total

with open('gen/surname_given_race.json', 'w') as f:
    json.dump(surname_given_race, f)
