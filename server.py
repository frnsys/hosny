import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from run import generate_population
from city import City
from threading import Thread

thread = None

class SocketsHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            emit('log', msg, broadcast=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')
socketio = SocketIO(app)


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
    global thread
    data = request.get_json()
    print(data)
    if thread is None:
        thread = Thread(target=run_simulation)
        thread.start()
    return jsonify(success=True)


@socketio.on('connect')
def on_connect(msg):
    print('client connected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
