import eventlet
eventlet.monkey_patch() # for flask_socketio message queue support

from app import create_app
from app.routes import routes
from flask_socketio import SocketIO

app = create_app(blueprints=[routes])
socketio = SocketIO(app, message_queue='redis://localhost:6379')
socketio.run(app, host='0.0.0.0', port=5000, debug=True)

