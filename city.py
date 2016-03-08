import json
import config
from itertools import chain
from cess import Simulation
from world.space import Space
from dateutil.relativedelta import relativedelta

world_data = json.load(open('data/world/nyc.json', 'r'))


class City(Simulation):
    def __init__(self, population, arbiter=None):
        super().__init__(population, arbiter)
        self.geography = Space([int(n) for n in world_data['puma_to_neighborhoods'].keys()],
                               world_data['edges'])

        # the world state
        self.date = config.START_DATE
        self.state = {
            'month': self.date.month,
            'year': self.date.year,
            'contact_rate': 0.4
        }

        for agent in population:
            self.geography.place_agent(agent, agent.puma)
            agent.goals = set(config.goals_for_agent(agent))

    def step(self):
        """one time step in the model (a day)"""
        super().step()
        self.date += relativedelta(days=1)
        self.state['month'] = self.date.month
        self.state['year'] = self.date.year

    def history(self):
        """get history of all agents"""
        if self.cluster:
            return list(chain.from_iterable([r['results'] for r in self.cluster.submit('call_agents', func='history')]))
        else:
            return [agent.history() for agent in self.agents]