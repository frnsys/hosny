import logging
import inspect
import asyncio
import traceback
from uuid import uuid4
from .client import Client
from .server import Server
from agent import AgentProxy

logger = logging.getLogger(__name__)


class Worker(Server):
    def __init__(self):
        self.agents = {}
        self.arbiter = None
        super().__init__()
        self.handlers = {
            'populate': self.populate,
            'call_agent': self.call_agent,
            'query_agent': self.query_agent,
            'call_agents': self.call_agents,
        }
        self.id = uuid4().hex

    @asyncio.coroutine
    def start(self, arbiter_host, arbiter_port, host='127.0.0.1', port=8899):
        """start the worker, specifying the arbiter host/port
        and host/port for the worker"""
        yield from super().start(host, port)
        self.arbiter = Client(arbiter_host, arbiter_port)
        try:
            yield from self.arbiter.send_recv({
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
        # so AgentProxies in this process reference this worker
        AgentProxy.worker = self
        self.agents = {a.id: a for a in data['agents']}
        return {'status': 'ok'}

    @asyncio.coroutine
    def call_agents(self, data):
        """call a method on all agents"""
        try:
            d = {'args': [], 'kwargs': {}}
            d.update(data)
            if self.agents:
                results = [getattr(agent, d['func'])(*d['args'], **d['kwargs']) for agent in self.agents.values()]
                if inspect.isgenerator(results[0]):
                    results = yield from asyncio.gather(*results)
            else:
                results = []
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
            result = getattr(agent, d['func'])(*d['args'], **d['kwargs'])
            if inspect.isgenerator(result):
                result = yield from result
            return result

        # pass request to the arbiter
        else:
            d['cmd'] = 'call_agent'
            return (yield from self.arbiter.send_recv(d))

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
            data['cmd'] = 'query_agent'
            return (yield from self.arbiter.send_recv(data))
