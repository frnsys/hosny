import asyncio
from cluster import Cluster, proxy_agents


class Simulation():
    def __init__(self, agents, arbiter=None):
        """a agent-based simulation.
        if you specify a connection tuple for `arbiter`, e.g. `('127.0.0.1', 8888)`,
        this will distribute the agents to the arbiter's cluster"""
        self.agents = agents
        self.state = {}

        if arbiter is not None:
            # distribute agents across cluster
            for agent in agents:
                proxy_agents(agent)

            host, port = arbiter
            self.cluster = Cluster(host, port)
            self.cluster.submit('populate', agents=agents)
        else:
            self.cluster = None

    def step(self):
        """run the simulation one time-step"""
        if self.cluster is not None:
            # each node steps over its agents
            self.cluster.submit('call_agents', func='step', args=(self.state,))
        else:
            loop = asyncio.get_event_loop()
            tasks = [agent.step(self.state) for agent in self.agents]
            loop.run_until_complete(asyncio.wait(tasks))