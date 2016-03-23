import random
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
    global queued_players

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

    # setup queued players
    for id in queued_players:
        players.append(id)
        person = random.choice([p for p in model.people if p.sid == None])
        person.sid = id
        socketio.emit('person', person.as_json(), namespace='/player', room=id)
    queued_players = []


@celery.task
def step_simulation():
    """steps through one month of the simulation"""
    global players
    global model
    _, n_days = monthrange(model.state['year'], model.state['month'])
    for _ in range(n_days):
        model.step()

    socketio = SocketIO(message_queue='redis://localhost:6379')
    socketio.emit('simulation', {'success': True}, namespace='/simulation')

    # choose a legislation proposer for the next month
    if players:
        print('CHOOSING PROPOSER')
        proposer = random.choice(players)
        socketio.emit('propose', {'proposals': model.government.proposal_options(model)}, room=proposer, namespace='/player')


@celery.task
def choose_proposer():
    global model
    if players:
        proposer = random.choice(players)
        socketio = SocketIO(message_queue='redis://localhost:6379')
        socketio.emit('propose', {'proposals': model.government.proposal_options(model)}, room=proposer, namespace='/player')


@celery.task
def start_vote(prop):
    global proposal
    proposal = prop
    socketio = SocketIO(message_queue='redis://localhost:6379')
    socketio.emit('vote', {'proposal': proposal}, namespace='/player')


votes = []
players = []
proposal = None
queued_players = []


def check_votes():
    global votes
    global players
    global model
    global proposal
    print('n_votes', len(votes))
    print('n_players', len(players))
    if len(votes) >= len(players) and proposal is not None:
        # vote has concluded
        print('vote done!')
        yay = sum(1 if v else -1 for v in votes if v is not None)
        if yay > 0:
            model.government.apply_proposal(proposal, model)
        proposal = None


@celery.task
def record_vote(vote):
    global votes
    print('received vote', vote)
    votes.append(vote)
    check_votes()


@celery.task
def add_player(id):
    global players
    global model
    global queued_players
    if model is not None:
        players.append(id)
        person = random.choice([p for p in model.people if p.sid == None])
        person.sid = id
        socketio = SocketIO(message_queue='redis://localhost:6379')
        socketio.emit('person', person.as_json(), namespace='/player', room=id)
    else:
        queued_players.append(id)
    print('registered', id)


@celery.task
def remove_player(id):
    global players
    global model
    if id in players:
        person = next((p for p in model.people if p.sid == id), None)
        players.remove(id)
        person.sid = None
        print('DEregistered', id)
        check_votes()
