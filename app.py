import eventlet
eventlet.monkey_patch() # for flask_socketio message queue support

from app import create_app
from app.routes import routes, handlers
from flask_socketio import SocketIO

app = create_app(blueprints=[routes])
socketio = SocketIO(app, message_queue='redis://localhost:6379', ping_timeout=1)

# have to do this manually
for msg, v in handlers.items():
    ns = v.get('namespace', '/')
    socketio.on(msg, namespace=ns)(v['func'])

@socketio.on('connect', namespace='/simulation')
def foo():
    print('SIMULATION CONNECTED')

socketio.run(app, host='0.0.0.0', port=5000, debug=True)
