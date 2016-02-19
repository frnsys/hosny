import asyncio
from .client import Client
from agent import Agent, AgentProxy


class Cluster(Client):
    def __init__(self, host, port):
        super().__init__(host, port)

    def submit(self, command, **data):
        """submit a command (and optionally data) to the arbiter"""
        data.update({'cmd': command})

        # assuming the script controlling the cluster is synchronous
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.send_recv(data))
        for result in results:
            if 'exception' in result:
                print(result['traceback'])
        return results


def proxy_agents(agent):
    """recursively replace all Agent references in the agent to AgentProxy"""
    for k, v in agent.__dict__.items():
        if isinstance(v, list):
            setattr(agent, k, [AgentProxy(o) if isinstance(o, Agent) else o for o in v])
        elif isinstance(v, Agent):
            setattr(agent, k, AgentProxy(v))
        else:
            try:
                proxy_agents(v)
            except AttributeError:
                pass
