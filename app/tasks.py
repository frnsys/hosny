import logging
from city import City
from people import Person
from celery import Celery
from calendar import monthrange
from flask_socketio import SocketIO
from run import generate_population, load_population
from .handlers import SocketsHandler
from app import create_app


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'], include=['app.tasks'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


app = create_app()
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)


# ehhh hacky
model = None
logger = logging.getLogger('simulation')


@celery.task
def setup_simulation(given, config):
    """prepare the simulation"""
    global model

    # don't redundantly add the handler
    if model is None:
        logger.setLevel(logging.INFO)
        sockets_handler = SocketsHandler()
        logger.addHandler(sockets_handler)

    # pop = generate_population(100)
    person = Person.generate(2005, given=given)
    print('YOU ARE', person)
    print('YOUR JOB IS', person.occupation)
    pop = load_population('data/population.json')
    pop = pop[:200] # limit to 200 for now
    pop.append(person) # TODO build out your social network
    model = City(pop, config)

    # send population to the frontend
    socketio = SocketIO(message_queue='redis://localhost:6379')
    socketio.emit('setup', {
        'population': [p.as_json() for p in pop],
        'buildings': [{'id': b.id} for b in model.buildings]
    }, namespace='/simulation')


@celery.task
def step_simulation():
    """steps through one month of the simulation"""
    _, n_days = monthrange(model.state['year'], model.state['month'])
    for _ in range(n_days):
        model.step()

    # send population to the frontend
    socketio = SocketIO(message_queue='redis://localhost:6379')
    socketio.emit('simulation', {'success': True}, namespace='/simulation')
