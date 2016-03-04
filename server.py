import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from celery import Celery
from city import City
from run import generate_population

class SocketsHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            emit('log', msg, broadcast=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')
socketio = SocketIO(app)

app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)

@celery.task
def run_simulation():
    logger = logging.getLogger('people')
    logger.setLevel(logging.INFO)
    logger.addHandler(SocketsHandler())

    pop = generate_population(100)
    model = City(pop)
    for _ in range(100):
        model.step()


@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    print(data)
    run_simulation.delay()
    return jsonify(success=True)


@socketio.on('connect')
def on_connect(msg):
    print('client connected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
