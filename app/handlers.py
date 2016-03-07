import logging
from flask_socketio import SocketIO


class SocketsHandler(logging.Handler):
    def emit(self, record):
        if not hasattr(self, 'socketio'):
            self.socketio = SocketIO(message_queue='redis://localhost:6379')
        try:
            msg = self.format(record)
            self.socketio.emit('log', {'msg': msg})
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
