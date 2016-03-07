from flask import Blueprint, jsonify, render_template, request
from .tasks import run_simulation

routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    return render_template('index.html')


@routes.route('/simulate', methods=['POST'])
def simulate():
    print('SIMULATION REQUEST RECEIVED')
    data = request.get_json()
    race = int(data['race'])
    education = int(data['education'])
    employment = int(data['employment'])
    run_simulation.delay({'race': race, 'education': education, 'employed': employment})
    return jsonify(success=True)
