"""
the simulation
"""

import json
import config
import random
from mesa import Model
from mesa.time import RandomActivation
from scipy import stats
from people import Person
from world import work, social
from world.space import Space
from dateutil.relativedelta import relativedelta

world_data = json.load(open('data/world/nyc.json', 'r'))


class City(Model):
    def __init__(self, population):
        self.schedule = RandomActivation(self)
        self.geography = Space([int(n) for n in world_data['puma_to_neighborhoods'].keys()],
                               world_data['edges'])

        # the world state
        self.date = config.START_DATE
        self.state = {
            'time': config.START_HOUR,
            'month': self.date.month,
            'year': self.date.year
        }

        self.pop = []
        for i in range(population):
            agent = Person.generate(config.START_DATE.year)
            self.geography.place_agent(agent, agent.puma)
            self.schedule.add(agent)
            self.pop.append(agent)
            print(agent, 'is moving into', agent.neighborhood)
            print(','.join([agent.occupation, str(agent.sex), str(agent.race), agent.neighborhood, str(agent.education), str(agent.rent)]))

        social_network = social.social_network(self.pop, base_prob=0.4)
        for i, person in enumerate(self.pop):
            person.friends = [self.pop[j] for _, j in social_network.edges(i)]

    def step(self):
        """one time step in the model (an hour)"""
        self.schedule.step()
        self._update_datetime()

    def _update_datetime(self):
        next = self.date + relativedelta(hours=1)
        if next.day != self.date.day:
            self.state['time'] = config.START_HOUR
        else:
            self.state['time'] += 1
        self.state['month'] = next.month
        self.state['year'] = next.month
        self.date = next

    def affect(self, agent):
        """apply random effects to agent"""
        # TODO better structure this section?

        # if an agent ends the day with <= 0 health, they are dead
        if agent.state['health'] <= 0:
            agent.dead = True
            return

        # getting sick
        if random.random() < config.SICK_PROB:
            agent.state['health'] -= stats.beta.rvs(2, 10)

        if agent.state['employed'] == 1:
            # wage change
            if random.random() < 1/365: # arbitrary probability, what should this be?
                change = work.income_change(self.date.year, self.date.year + 1, agent.sex, agent.race, agent.income_bracket)
                agent.state['income'] += change # TODO this needs to change their income bracket if appropriate
            else:
                employment_dist = work.employment_dist(self.date.year, self.date.month, agent.sex, agent.race)
                p_unemployed = employment_dist['unemployed']/365 # kind of arbitrary denominator, what should this be?
                # fired
                if random.random() < p_unemployed:
                    agent.state['employed'] = 0

        # if the agent fails to pay rent/mortgage 3 months in a row,
        # they get evicted/lose their house
        if agent.state['rent_fail'] >= 3:
            # what are the effects of this?
            pass # TODO

        # tick goals/check failures
        remaining_goals = []
        for goal in agent.goals:
            goal.tick()
            if goal.time <= 0:
                agent.state = goal.fail(agent.state)
            else:
                remaining_goals.append(goal)
        agent.goals = remaining_goals


def run_simulation(population, days):
    model = City(population)
    hours = 0
    while hours <= days * 24:
        model.step()
        hours += 1


if __name__ == '__main__':
    run_simulation(10, 10)