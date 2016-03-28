import json
import click
from datetime import datetime
from people import Person
from .social import social_network

START_DATE = datetime(day=1, month=1, year=2005)


def load_population(path):
    raw = json.load(open(path, 'r'))
    pop = [Person(**p) for p in raw]

    # update ids
    for p, p_raw in zip(pop, raw):
        p.id = p_raw['id']
        p.friends = p_raw['friends']

    # setup friends
    for p in pop:
        friends = []
        for f in p.friends:
            friend = next(p_ for p_ in pop if p_.id == f)
            friends.append(friend)
        p.friends = friends
    return pop


def save_population(pop, path):
    json_pop = [p.as_json() for p in pop]
    with open(path, 'w') as f:
        json.dump(json_pop, f)


def generate_population(n):
    population = []

    with click.progressbar(range(n), label='populating...') as n:
        for i in n:
            agent = Person.generate(START_DATE.year)
            population.append(agent)

    social_net = social_network(population, base_prob=0.4)
    for i, person in enumerate(population):
        person.friends = [population[j] for _, j in social_net.edges(i)]
    print('avg n of friends', sum(len(p.friends) for p in population)/len(population))
    return population
