import os
import json
import config
import random
from sim import Simulation
from scipy import stats
from world.space import Space
from dateutil.relativedelta import relativedelta
from datetime import datetime

world_data = json.load(open('data/world/nyc.json', 'r'))


class City(Simulation):
    def __init__(self, population, arbiter=None):
        super().__init__(population, arbiter)
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
            agent.goals = set(config.goals_for_agent(agent))

        session_id = datetime.now().isoformat()
        log_dir = 'logs/{}'.format(session_id)
        os.makedirs(log_dir)
        if self.cluster:
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