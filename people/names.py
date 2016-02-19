import json
import random
from util import random_choice

with open('data/names/gen/surname_given_race.json', 'r') as f:
    surname_given_race = json.load(f)
with open('data/names/gen/name_given_sex.json', 'r') as f:
    name_given_sex = json.load(f)

race_map = {
    # in the PUMS data, "white" encompasses "hispanic" as well
    'white': ['white', 'hispanic'],
    'black': 'black',
    'api': 'api',
    'chinese': 'api',
    'japanese': 'api',
    'aian': 'aian',
    'two': '2prace',
    'three_plus': '2prace',
    'other': '2prace'
}


def generate_name(sex, race):
    name = random_choice(name_given_sex[sex.name].items())
    race = race_map[race.name]
    if isinstance(race, list):
        race = random.choice(race)
    surname = random_choice(surname_given_race[race].items())
    return '{} {}'.format(name, surname).title()
