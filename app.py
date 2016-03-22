import eventlet
eventlet.monkey_patch() # for flask_socketio message queue support

from app import create_app, socketio
from app.routes import routes, handlers

app = create_app(blueprints=[routes])

# have to do this manually
for msg, v in handlers.items():
    ns = v.get('namespace', '/')
    socketio.on(msg, namespace=ns)(v['func'])

@socketio.on('connect')
def foo():
    pass

socketio.run(app, host='0.0.0.0', port=5000, debug=True)
