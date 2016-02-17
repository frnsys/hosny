import asyncio
from client import Client


class Commander(Client):
    def __init__(self, host, port):
        super().__init__(host, port)

    def submit(self, command, **data):
        """submit a command (and optionally data) to the arbiter"""
        data.update({'cmd': command})
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.send_recv(data))
