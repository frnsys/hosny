from . import protocol
from asyncio import streams, coroutine


class Client():
    def __init__(self, host, port):
        self.host = host
        self.port = port

    @coroutine
    def send_recv(self, data):
        """send data to a server, get a response"""
        reader, writer = yield from streams.open_connection(self.host, self.port)
        yield from protocol.write(writer, data)
        resp = yield from protocol.read(reader)
        writer.close()
        return resp
