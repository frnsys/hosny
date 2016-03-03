import logging
from . import protocol
from asyncio import streams, coroutine, Task

logger = logging.getLogger(__name__)


class Server():
    def __init__(self):
        self.server = None

        # task -> (reader, writer)
        self.clients = {}

        # cmd -> coroutine
        self.handlers = {}

    def _accept_client(self, client_reader, client_writer):
        """manage new client connections"""
        task = Task(self._handle_client(client_reader, client_writer))
        self.clients[task] = (client_reader, client_writer)

        def client_done(task):
            del self.clients[task]

        task.add_done_callback(client_done)

    @coroutine
    def _handle_client(self, client_reader, client_writer):
        """handle a client's request and serve it a response"""
        while True:
            try:
                data = (yield from protocol.read(client_reader))
                if not data: # an empty string means the client disconnected
                    client_writer.close()
                    break
                resp = yield from self.respond(data)
                yield from protocol.write(client_writer, resp)

            # disconnected
            except EOFError:
                break

    @coroutine
    def respond(self, data):
        """generate a client response, based on submitted data.
        this should return a dictionary (i.e. handlers should return dicts).
        by default this looks for a handler that matches the specified `cmd`"""
        cmd = data['cmd']
        try:
            return (yield from self.handlers[cmd](data))
        except KeyError:
            return {'exception': 'handler not found for {}'.format(cmd)}

    @coroutine
    def start(self, host, port):
        """start the server"""
        logger.info('started at {}:{}'.format(host, port))
        self.server = yield from streams.start_server(self._accept_client, host, port, reuse_address=True)

    @coroutine
    def stop(self):
        """stop the server"""
        if self.server is not None:
            self.server.close()
            yield from self.server.wait_closed()
            self.server = None
