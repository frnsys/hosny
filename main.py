"""
the simulation
"""

import os
import json
import config
import random
from sim import Simulation
from scipy import stats
from people import Person
from world import work, social
from world.space import Space
from dateutil.relativedelta import relativedelta
from datetime import datetime

with open('data/world/nyc.json', 'r') as f:
    world_data = json.load(f)

# precompute and cache to save a lot of time
emp_dist = work.precompute_employment_dist()

class City(Simulation):
    def __init__(self, population, distributed=False):
        super().__init__(population, distributed)
        self.geography = Space([int(n) for n in world_data['puma_to_neighborhoods'].keys()],
                               world_data['edges'])

        # the world state
        self.date = config.START_DATE
        self.state = {
            'time': config.START_HOUR,
            'month': self.date.month,
            'year': self.date.year
        }

        for agent in population:
            self.geography.place_agent(agent, agent.puma)

        session_id = datetime.now().isoformat()
        log_dir = 'logs/{}'.format(session_id)
        os.makedirs(log_dir)
        if self.distributed:
            self.cluster.submit('call_agents', func='set_logger', args=(log_dir,))
        else:
            for agent in self.agents:
                agent.set_logger(log_dir)

    def step(self):
        """one time step in the model (an hour)"""
        super().step()
        self._update_datetime()

    def _update_datetime(self):
        next = self.date + relativedelta(hours=1)
        if next.day != self.date.day:
            print('~~~ NEW DAY ~~~')
            self.state['time'] = config.START_HOUR
        else:
            self.state['time'] += 1
        self.state['month'] = next.month
        self.state['year'] = next.year
        self.date = next

    def affect(self, agent):
        """apply random effects to agent"""
        # TODO better structure this section?
        if self.state['time'] != config.START_HOUR:
            return

        # if an agent ends the day with <= 0 health, they are dead
        if agent['health'] <= 0:
            agent.dead = True
            return

        # getting sick
        if random.random() < config.SICK_PROB:
            agent['health'] -= stats.beta.rvs(2, 10)

        if agent['employed'] == 1:
            # wage change
            if random.random() < 1/365: # arbitrary probability, what should this be?
                change = work.income_change(self.date.year, self.date.year + 1, agent.sex, agent.race, agent.income_bracket)
                agent['income'] += change # TODO this needs to change their income bracket if appropriate
            else:
                employment_dist = emp_dist[self.date.year][self.date.month][agent.race.name][agent.sex.name]
                p_unemployed = employment_dist['unemployed']/365 # kind of arbitrary denominator, what should this be?
                # fired
                if random.random() < p_unemployed:
                    agent['employed'] = 0

        # if the agent fails to pay rent/mortgage 3 months in a row,
        # they get evicted/lose their house
        if agent['rent_fail'] >= 3:
            # what are the effects of this?
            pass # TODO

        # tick goals/check failures
        remaining_goals = set()
        for goal in agent.goals:
            goal.tick()
            if goal.time <= 0:
                agent.state = goal.fail(agent.state)
            else:
                remaining_goals.add(goal)
        agent.goals = remaining_goals


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


def run_simulation(population, days):
    model = City(population, distributed=True)
    hours = 0
    while hours <= days * 24:
        model.step()
        hours += 1


if __name__ == '__main__':
    from time import time
    from datetime import timedelta

    population = generate_population(2)

    print('running simulation...')
    s = time()
    run_simulation(population, 5)
    print('elapsed:', str(timedelta(seconds=time() - s)))