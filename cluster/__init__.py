import logging
import asyncio
from .client import Client

logger = logging.getLogger(__name__)


class Cluster(Client):
    def __init__(self, host, port):
        super().__init__(host, port)

    def submit(self, command, **data):
        """submit a command (and optionally data) to the arbiter"""
        data.update({'cmd': command})
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.send_recv(data))
        for result in results:
            if 'exception' in result:
                # logger.exception(result['traceback'])
                print(result['traceback'])


class AgentProxy():
    def __init__(self, id, worker):
        self.id = id
        self.worker = worker

    @asyncio.coroutine
    def __getitem__(self, key):
        return (yield from self.worker.query_agent({
            'id': self.id,
            'key': key
        }))

    def __repr__(self):
        return 'AgentProxy({})'.format(self.id)
