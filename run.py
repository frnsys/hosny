import click
import config
import logging
from city import City
from world import social
from people import Person
from time import time
from datetime import timedelta


@click.command()
@click.argument('population', 'number of simulated citizens', type=int)
@click.argument('days', '(simulated) days to run', type=int)
@click.argument('arbiter', default=[])
def run(population, days, arbiter):
    run_simulation(population, days, arbiter)


def run_simulation(population, days, arbiter):
    logging.basicConfig(level=logging.INFO)

    if arbiter:
        host, port = arbiter.split(':')
        arbiter = (host, int(port))
    else:
        arbiter = None

    print('generating population...')
    pop = generate_population(population)
    model = City(pop, arbiter=arbiter)

    s = time()
    print('running simulation...')
    hours = 0
    while hours <= days * 24:
        model.step()
        hours += 1
    print('elapsed:', str(timedelta(seconds=time() - s)))

    print('SALIENT HISTORIES~~~~~')
    print(model.history())


def generate_population(n):
    population = []
    for i in range(n):
        agent = Person.generate(config.START_DATE.year)
        population.append(agent)
        print(agent, 'is moving into', agent.neighborhood)
        print('  ', ','.join([agent.occupation, str(agent.sex), str(agent.race), agent.neighborhood, str(agent.education), str(agent.rent)]))

    social_network = social.social_network(population, base_prob=0.4)
    for i, person in enumerate(population):
        person.friends = [population[j] for _, j in social_network.edges(i)]
    return population


if __name__ == '__main__':
    run()