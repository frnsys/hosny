from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(message_queue='redis://localhost:6379', ping_timeout=1)


def create_app(package_name=__name__, blueprints=[], static_folder='static', template_folder='templates', **config_overrides):
    app = Flask(package_name,
                static_url_path='/static',
                static_folder=static_folder,
                template_folder=template_folder)

    # apply overrides
    app.config.update(config_overrides)

    # register blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    socketio.init_app(app)

    return app
