import logging
from flask_socketio import SocketIO


class SocketsHandler(logging.Handler):
    def emit(self, record):
        if not hasattr(self, 'socketio'):
            self.socketio = SocketIO(message_queue='redis://localhost:6379')
        try:
            # format: 'CHAN:ID:NAME:MSG'
            chan, id, name, msg = record.getMessage().split(':', 3)
            self.socketio.emit(chan, {'msg': msg, 'name': name, 'id': id})
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
