"""
the simulation
"""

import json

world_data = json.load(open('data/world/nyc.json', 'r'))

from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector

from people import Person
from world.space import Space


class City(Model):
    def __init__(self, population):
        self.schedule = SimultaneousActivation(self)


        self.geography = Space([int(n) for n in world_data['puma_to_neighborhoods'].keys()],
                               world_data['edges'])

        self.population = population

        self.datacollector = DataCollector(
            # model-level
            {},

            # agent-level
            {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1]})

        for i in range(population):
            agent = Person.generate()
            self.geography.place_agent(agent, agent.puma)
            self.schedule.add(agent)
            print(agent, 'is moving into', agent.neighborhood)
            print('  ', agent.occupation)

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)


if __name__ == '__main__':
    model = City(100)
    #while True:
        #model.step()