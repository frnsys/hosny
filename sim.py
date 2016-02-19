import asyncio
from cluster import Cluster


class Simulation():
    def __init__(self, agents, distributed=False, arbiter_host='127.0.0.1', arbiter_port=8888):
        self.agents = agents
        self.state = {}

        self.distributed = distributed
        if distributed:
            # distribute agents across cluster
            self.cluster = Cluster(arbiter_host, arbiter_port)
            self.cluster.submit('populate', agents=agents)

    def step(self):
        if self.distributed:
            # each node steps over its agents
            self.cluster.submit('call_agents', func='step', args=(self.state,))
        else:
            tasks = [agent.step(self.state) for agent in self.agents]
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait(tasks))