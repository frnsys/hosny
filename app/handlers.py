import json
import logging
from flask_socketio import SocketIO


class SocketsHandler(logging.Handler):
    def emit(self, record):
        if not hasattr(self, 'socketio'):
            self.socketio = SocketIO(message_queue='redis://localhost:6379')
        try:
            # format: 'CHAN:DATA'
            chan, datastr = record.getMessage().split(':', 1)
            self.socketio.emit(chan, json.loads(datastr))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
