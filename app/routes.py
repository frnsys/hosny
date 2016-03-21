from flask import Blueprint, jsonify, render_template, request, abort
from .tasks import step_simulation, setup_simulation
from run import load_population

routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    return render_template('index.html')


@routes.route('/game')
def game():
    return render_template('game.html')


@routes.route('/city')
def city():
    return render_template('city.html')


@routes.route('/step', methods=['POST'])
def step():
    print('STEP REQUEST RECEIVED')
    step_simulation.delay()
    return jsonify(success=True)


@routes.route('/setup', methods=['POST'])
def setup():
    print('SIMULATION REQUEST RECEIVED')
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
