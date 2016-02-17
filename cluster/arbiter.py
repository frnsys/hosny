import math
import asyncio
import logging
from client import Client
from server import Server

logger = logging.getLogger(__name__)


class Arbiter(Server):
    """the arbiter manages all of the workers"""

    def __init__(self):
        self.agents = {}
        self.workers = {}
        self.ncores = {}
        self.commanders = {}
        super().__init__()
        self.handlers = {
            'step': self.step,
            'register': self.register,
            'populate': self.populate,
            'call_agent': self.call_agent,
            'query_agent': self.query_agent,
        }

    @asyncio.coroutine
    def step(self, data):
        # world_state = data.pop('world_state')
        tasks = []
        for id, worker in self.workers.items():
            tasks.append(asyncio.Task(worker.send_recv({'cmd': 'step'})))
        yield from asyncio.gather(*tasks)
        return {'success': 'ok'}

    @asyncio.coroutine
    def populate(self, data):
        agents = data['agents']
        ncores = sum(self.ncores.values())
        agents_per_core = math.ceil(len(agents)/ncores)
        print('total ncores', ncores)
        print('agents per core', agents_per_core)

        tasks = []
        i = 0
        for id, worker in self.workers.items():
            nagents = self.ncores[id] * agents_per_core
            print('from:', i, 'to:', nagents)
            to_send = agents[i:i+nagents]
            tasks.append(asyncio.Task(worker.send_recv({'cmd': 'populate', 'agents': to_send})))
            # keep track of where agents are
            for agent in to_send:
                self.agents[agent.id] = id
            i += nagents
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
                print('registered {} at {}:{}'.format(type, host, port))
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


if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = Arbiter()
    loop.run_until_complete(server.start(loop))

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(server.stop())
        loop.close()

