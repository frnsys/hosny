import sys
import click
import asyncio
import logging
import traceback
import threading
import multiprocessing
from logging import FileHandler
from cluster.worker import Worker
from cluster.arbiter import Arbiter
from concurrent.futures import ProcessPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(message)s')

def _splitconn(conn):
    host, port = conn.split(':')
    return host, int(port)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('conn', 'host and port to run the arbiter on')
def arbiter(conn):
    """start an arbiter"""
    host, port = _splitconn(conn)
    loop = asyncio.get_event_loop()

    # creates a server and starts listening to TCP connections
    server = Arbiter()
    loop.run_until_complete(server.start(host, port))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(server.stop())
        loop.close()


@cli.command()
@click.argument('conn', 'arbiter host and port')
@click.argument('start_port', 'starting port for workers', default=8880)
@click.argument('cores', 'number of cores to use; 0 for all', default=0)
def node(conn, start_port, cores):
    """start a node with multiple workers"""
    host, port = _splitconn(conn)
    Node().start(host, port, start_port, cores)


def start_worker(arbiter_host, arbiter_port, port):
    """start a worker"""
    loop = asyncio.get_event_loop()
    work = Worker()
    loop.run_until_complete(work.start(arbiter_host, arbiter_port, port=port))

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(work.stop())
        loop.close()


@cli.command()
@click.argument('conn', 'arbiter host and port')
@click.argument('port', 'port to run worker on', default=8880)
def worker(conn, port):
    host, port = _splitconn(conn)
    start_worker(host, port)


class Node():
    def start(self, arbiter_host, arbiter_port, start_port, cores):
        cpus = multiprocessing.cpu_count()
        if cores > 0:
            cores = min(cpus, cores)
        else:
            cores = max(1, cpus - cores)

        logger.info('starting {} workers'.format(cores))
        with ProcessPoolExecutor(max_workers=cores) as executor:
            port = start_port
            for _ in range(cores):
                executor.submit(start_worker, arbiter_host, arbiter_port, port)
                port += 1

            while True:
                pass


class MPLogHandler(logging.Handler):
    """a multiprocessing-compatible file log handler -
    all processes log to the same file"""
    def __init__(self, fname):
        logging.Handler.__init__(self)

        self._handler = FileHandler(fname)
        self.queue = multiprocessing.Queue(-1)

        thrd = threading.Thread(target=self.receive)
        thrd.daemon = True
        thrd.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self):
        while True:
            try:
                record = self.queue.get()
                self._handler.emit(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                break
            except:
                traceback.print_exc(file=sys.stderr)

    def send(self, s):
        self.queue.put_nowait(s)

    def _format_record(self, record):
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            # dummy = self.format(record)
            record.exc_info = None
        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        self._handler.close()
        logging.Handler.close(self)


if __name__ == '__main__':
    logger = logging.getLogger('cluster.worker')
    logger.addHandler(MPLogHandler('/tmp/node.log'))
    cli()
