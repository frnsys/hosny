import logging
import asyncio
import multiprocessing
from uuid import uuid4
from client import Client
from server import Server

logger = logging.getLogger(__name__)


class Worker(Server):
    def __init__(self):
        self.agents = {}
        self.client = None # connection to arbiter
        super().__init__()
        self.handlers = {
            'step': self.step,
            'populate': self.populate,
            'call_agent': self.call_agent,
            'query_agent': self.query_agent,
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
                'ncores': multiprocessing.cpu_count(),
                'type': 'worker'})
        except ConnectionRefusedError:
            logger.exception('could not connect to arbiter at {}:{}'.format(host, port))
            raise

    @asyncio.coroutine
    def step(self, data):
        """advance each of this worker's agents a step"""
        coros = []
        for agent in self.agents.values():
            coros.append(agent.step(self))
        if coros:
            yield from asyncio.wait(coros)
        return {'status': 'ok'}

    @asyncio.coroutine
    def populate(self, data):
        """populate this worker with agents"""
        self.agents = {a.id: a for a in data['agents']}
        return {'status': 'ok'}

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
            return agent[data['key']]

        # pass request to the arbiter
        else:
            return (yield from self.client.send_recv(data))


if __name__ == '__main__':
    import sys
    import asyncio
    loop = asyncio.get_event_loop()
    worker = Worker()
    loop.run_until_complete(worker.start(loop, '127.0.0.1', 8888, port=sys.argv[1]))

    # creates a client and connects to our server
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(worker.stop())
        loop.close()

