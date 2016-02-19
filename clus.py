import sys
import asyncio
import logging
from cluster.worker import Worker
from cluster.node import Node
from cluster.arbiter import Arbiter

logging.basicConfig(level=logging.INFO, format='%(message)s')


def start_arbiter(host, port):
    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = Arbiter()
    loop.run_until_complete(server.start(loop))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(server.stop())
        loop.close()


def start_workers(arbiter_host, arbiter_port):
    start_port = 8880
    Node().start(arbiter_host, arbiter_port, start_port)


def start_worker(arbiter_host, arbiter_port):
    loop = asyncio.get_event_loop()
    worker = Worker()
    loop.run_until_complete(worker.start(loop, arbiter_host, arbiter_port, port=8880))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(worker.stop())
        loop.close()


if __name__ == '__main__':
    cmd = sys.argv[1]
    host, port = sys.argv[2].split(':')
    port = int(port)

    if cmd == 'arbiter':
        start_arbiter(host, port)
    elif cmd == 'node':
        start_workers(host, port)
    elif cmd == 'worker':
        start_worker(host, port)
    else:
        print('`{}` is not a valid command')
        sys.exit(1)