from . import protocol
from asyncio import streams, coroutine


class Client():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.streams = {}

    @coroutine
    def _get_stream(self):
        """get an unused stream"""
        stream = None
        for stream_, open in self.streams.items():
            reader, writer = stream_
            if writer.transport._closing:
                del self.streams[stream_]
            elif open:
                stream = stream_
                break
        if stream is None:
            stream = yield from streams.open_connection(self.host, self.port)
        self.streams[stream] = False
        return stream

    @coroutine
    def send_recv(self, data):
        """send data to a server, get a response"""
        stream = yield from self._get_stream()
        reader, writer = stream
        yield from protocol.write(writer, data)
        resp = yield from protocol.read(reader)
        self.streams[stream] = True
        return resp
