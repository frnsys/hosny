import logging
import asyncio
import multiprocessing
from .worker import Worker
from concurrent.futures import ProcessPoolExecutor

import sys
import traceback
import threading
from logging import FileHandler


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


logger = logging.getLogger('cluster.worker')
logger.addHandler(MPLogHandler('/tmp/node.log'))


def start_worker(arbiter_host, arbiter_port, port):
    loop = asyncio.get_event_loop()
    worker = Worker()
    loop.run_until_complete(worker.start(loop, arbiter_host, arbiter_port, port=port))

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(worker.stop())
        loop.close()


class Node():
    def start(self, arbiter_host, arbiter_port, start_port):
        ncores = multiprocessing.cpu_count()

        logger.info('starting {} workers'.format(ncores))
        with ProcessPoolExecutor(max_workers=ncores) as executor:
            port = start_port
            for _ in range(ncores):
                executor.submit(start_worker, arbiter_host, arbiter_port, port)
                port += 1

            while True:
                pass