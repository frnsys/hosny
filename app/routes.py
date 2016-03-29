from flask import Blueprint, jsonify, render_template, request, abort
from .tasks import step_simulation, setup_simulation, record_vote, add_player, remove_player, choose_proposer, start_vote, reset, add_client
from world.population import load_population

routes = Blueprint('routes', __name__)



def register_player():
    add_player.delay(request.sid)

def unregister_player():
    remove_player.delay(request.sid)


def register_simulation():
    """a new simulation frontend"""
    add_client.delay(request.sid)



# hacky, but doesn't seem to work any other way
handlers = {
    'connect': {
        '/player': register_player,
        '/simulation': register_simulation
    },
    'disconnect': {
        '/player': unregister_player,
    }
}


@routes.route('/')
def index():
    return render_template('city.html')


@routes.route('/graphs')
def graphs():
    return render_template('graphs.html')


@routes.route('/step', methods=['POST'])
def step():
    step_simulation.delay()
    return jsonify(success=True)


@routes.route('/setup', methods=['POST'])
def setup():
    data = request.get_json()
    person = data['person']
    race = int(person['race'])
    education = int(person['education'])
    employment = int(person['employment'])
    setup_simulation.delay(
        {'race': race, 'education': education, 'employed': employment},
        data['world']
    )
    return jsonify(success=True)


@routes.route('/player')
def player():
    return render_template('player.html')


@routes.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    vote = data.get('vote', None)
    record_vote.delay(vote)
    return jsonify(success=True)


@routes.route('/propose', methods=['POST'])
def propose():
    data = request.get_json()
    proposal = data.get('proposal', None)
    if proposal is None:
        choose_proposer.delay()
    else:
        print(proposal)
        start_vote.delay(proposal)
    return jsonify(success=True)


pop = load_population('data/population.json')
@routes.route('/person/<id>')
def person(id):
    # eh hacky but ok for this scale
    per = None
    for p in pop:
        if p.id == id:
            per = p
            break
    if per is None:
        abort(404)
    return jsonify(**per.as_json())


@routes.route('/reset')
def reset_sim():
    """reset the simulation"""
    reset.delay()
    return 'ok resetted'
