import random
import logging
from city import City
from celery import Celery
from calendar import monthrange
from flask_socketio import SocketIO
from world.population import load_population #, generate population
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


def socketio():
    return SocketIO(message_queue='redis://localhost:6379')


app = create_app()
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)


# ehhh hacky
model = None
votes = []
players = []
proposal = None
queued_players = []
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

    pop = load_population('data/population.json')
    pop = pop[:200] # limit to 200 for now
    model = City(pop, config)

    # send population to the frontend
    s = socketio()
    s.emit('setup', {
        'population': [p.as_json() for p in pop],
        'buildings': [{'id': b.id} for b in model.buildings]
    }, namespace='/simulation')

    # setup queued players
    print('QUEUED PLAYERS')
    print(queued_players)
    for id in queued_players:
        players.append(id)
        person = random.choice([p for p in model.people if p.sid == None])
        person.sid = id
        s.emit('person', person.as_json(), namespace='/player', room=id)
        s.emit('joined', person.as_json(), namespace='/simulation')
    queued_players = []


@celery.task
def step_simulation():
    """steps through one month of the simulation"""
    _, n_days = monthrange(model.state['year'], model.state['month'])
    for _ in range(n_days):
        model.step()

    s = socketio()
    s.emit('simulation', {'success': True}, namespace='/simulation')

    # choose a legislation proposer for the next month
    if players:
        print('CHOOSING PROPOSER')
        proposer = random.choice(players)
        s.emit('propose', {'proposals': model.government.proposal_options(model)}, room=proposer, namespace='/player')


@celery.task
def choose_proposer():
    global proposal
    if players and proposal is None:
        proposer = random.choice(players)
        s = socketio()
        s.emit('propose', {'proposals': model.government.proposal_options(model)}, room=proposer, namespace='/player')


@celery.task
def start_vote(prop):
    global proposal
    proposal = prop
    socketio().emit('vote', {'proposal': proposal}, namespace='/player')
    # end_vote.apply_async(countdown=30)


def check_votes():
    global votes
    global proposal
    print('n_votes', len(votes))
    print('n_players', len(players))
    if len(votes) >= len(players) and proposal is not None:
        # vote has concluded
        print('vote done!')
        yay = sum(1 if v else -1 for v in votes if v is not None)
        print('yay votes', yay)
        if yay > 0:
            model.government.apply_proposal(proposal, model)
        proposal = None
        votes = []


@celery.task
def end_vote():
    global proposal
    if proposal is not None:
        # vote has concluded
        print('vote done! (timeout)')
        yay = sum(1 if v else -1 for v in votes if v is not None)
        if yay > 0:
            model.government.apply_proposal(proposal, model)
        proposal = None


@celery.task
def record_vote(vote):
    print('received vote', vote)
    votes.append(vote)
    check_votes()


@celery.task
def add_player(id):
    """adds a player to the game, assigning them an unassigned simulant.
    if the game is not ready, they are added to the player queue"""
    s = socketio()
    if model is not None:
        players.append(id)
        person = random.choice([p for p in model.people if p.sid == None])
        person.sid = id
        s.emit('person', person.as_json(), namespace='/player', room=id)
        s.emit('joined', person.as_json(), namespace='/simulation')
    else:
        queued_players.append(id)
        s.emit('joined_queue', {'id': id}, namespace='/simulation')
    print('registered', id)


@celery.task
def remove_player(id):
    """removes a player from the game, releasing their simulant"""
    s = socketio()
    if id in players:
        person = next((p for p in model.people if p.sid == id), None)
        players.remove(id)
        person.sid = None
        s.emit('left', person.as_json(), namespace='/simulation')

        # since player count has changed, re-check votes
        check_votes()
    elif id in queued_players:
        s.emit('left_queue', {'id': id}, namespace='/simulation')
    print('deregistered', id)


@celery.task
def reset():
    """reset the currently-running simulation"""
    global model
    global votes
    global proposal
    global players
    global queued_players
    model = None
    proposal = None
    votes = []
    players = []
    queued_players = []
