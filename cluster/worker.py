import logging
import inspect
import asyncio
import traceback
from uuid import uuid4
from .client import Client
from .server import Server
from cluster import AgentProxy

logger = logging.getLogger(__name__)


class Worker(Server):
    def __init__(self):
        self.agents = {}
        self.client = None # connection to arbiter
        super().__init__()
        self.handlers = {
            'populate': self.populate,
            'call_agent': self.call_agent,
            'query_agent': self.query_agent,
            'call_agents': self.call_agents,
        }
        self.id = uuid4().hex

    @asyncio.coroutine
    def start(self, loop, arbiter_host, arbiter_port, host='127.0.0.1', port=8899):
        """start the worker, specifying the arbiter host/port
        and host/port for the worker"""
        yield from super().start(loop, host, port)
        self.client = Client(arbiter_host, arbiter_port)
        try:
            yield from self.client.send_recv({
                'cmd': 'register',
                'id': self.id,
                'host': host,
                'port': port,
                'type': 'worker'})
        except ConnectionRefusedError:
            logger.exception('could not connect to arbiter at {}:{}'.format(host, port))
            raise

    @asyncio.coroutine
    def populate(self, data):
        """populate this worker with agents"""
        self.agents = {a.id: a for a in data['agents']}
        logger.info('populated with {} agents'.format(len(self.agents)))
        ids = list(self.agents.keys())
        id1 = ids[0]
        id2 = ids[1]
        self.agents[id2].friends = [AgentProxy(self.agents[id1].id, self)]
        logger.info('friends {}'.format(self.agents[id2].friends))
        return {'status': 'ok'}

    @asyncio.coroutine
    def call_agents(self, data):
        """call a method on all agents"""
        try:
            d = {'args': [], 'kwargs': {}}
            d.update(data)
            results = [getattr(agent, d['func'])(*d['args'], **d['kwargs']) for agent in self.agents.values()]
            if inspect.isgenerator(results[0]):
                results = yield from asyncio.gather(*results)
            return {'status': 'ok', 'results': results}
        except Exception as e:
            tb = traceback.format_exc()
            logger.exception(e)
            logger.exception(tb)
            return {'status': 'failed', 'exception': e, 'traceback': tb}

    @asyncio.coroutine
    def call_agent(self, data):
        """call a method on an agent and get the result"""
        d = {'args': [], 'kwargs': {}}
        d.update(data)
        id = d['id']

        # check locally
        if id in self.agents:
            agent = self.agents[id]
            return getattr(agent, d['func'])(*d['args'], **d['kwargs'])

        # pass request to the arbiter
        else:
            return (yield from self.client.send_recv(d))

    @asyncio.coroutine
    def query_agent(self, data):
        """query an agent's state"""
        id = data['id']

        # check locally
        if id in self.agents:
            agent = self.agents[id]
            return (yield from agent[data['key']])

        # pass request to the arbiter
        else:
            return (yield from self.client.send_recv(data))
