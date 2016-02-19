import math
import asyncio
import logging
from .client import Client
from .server import Server

logger = logging.getLogger(__name__)


class Arbiter(Server):
    """the arbiter manages all of the workers"""

    def __init__(self):
        self.agents = {}
        self.workers = {}
        self.commanders = {}
        super().__init__()
        self.handlers = {
            'register': self.register,
            'populate': self.populate,
            'call_agent': self.call_agent,
            'query_agent': self.query_agent,
            'call_agents': self.call_agents,
        }

    @asyncio.coroutine
    def call_agents(self, data):
        """call a method on all agents"""
        logger.info('calling `{}` on all agents'.format(data['func']))
        tasks = []
        for id, worker in self.workers.items():
            # just fwd call to workers
            tasks.append(asyncio.Task(worker.send_recv(data)))
        yield from asyncio.gather(*tasks)
        return {'success': 'ok'}

    @asyncio.coroutine
    def populate(self, data):
        agents = data['agents']
        agents_per_worker = math.ceil(len(agents)/len(self.workers))

        tasks = []
        i = 0
        for id, worker in self.workers.items():
            to_send = agents[i:i+agents_per_worker]
            tasks.append(asyncio.Task(worker.send_recv({
                'cmd': 'populate', 'agents': to_send})))

            # keep track of where agents are
            for agent in to_send:
                self.agents[agent.id] = id
            i += agents_per_worker
        yield from asyncio.gather(*tasks)
        return {'success': 'ok'}

    @asyncio.coroutine
    def register(self, data):
        id, type = data['id'], data['type']
        try:
            if type == 'worker':
                host, port = data['host'], data['port']
                self.workers[id] = Client(host, port)
                self.ncores[id] = data['ncores']
                logger.info('registered {} at {}:{}'.format(type, host, port))
            return {'success': 'ok'}
        except ConnectionRefusedError:
            logger.exception('could not connect to {}:{}'.format(host, port))
            raise

    @asyncio.coroutine
    def call_agent(self, data):
        """call a method on an agent and get the result"""
        id = data['id']

        # find worker that agent is at
        worker_id = self.agents[id]
        worker = self.workers[worker_id]

        # pass along the request to that worker, return the result
        return (yield from worker.send_recv(data))

    @asyncio.coroutine
    def query_agent(self, data):
        """query an agent's state"""
        id = data['id']

        # find worker that agent is at
        worker_id = self.agents[id]
        worker = self.workers[worker_id]

        # pass along the request to that worker, return the result
        return (yield from worker.send_recv(data))
