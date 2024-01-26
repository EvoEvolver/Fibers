from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from forest import build_dir, asset_dir
import sys


app = Flask(__name__, template_folder=build_dir, static_folder=asset_dir, static_url_path='/assets')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
tree = {}

import logging

log = logging.getLogger('werkzeug')
log.disabled = True
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None


@socketio.on('connect')
def handle_connect():
    emit('Connected!')


@socketio.on('requestTree')
def requestTree():
    emit('setTree', tree)


@app.route('/visualization')
def visualization():
    return render_template('index.html')


# update tree
@app.route('/updateTree', methods=['PUT'])
def updateTree():
    global tree
    # TODO: check if the tree is valid.
    tree = request.get_json()['tree']
    socketio.emit('setTree', tree)
    return "OK"


if __name__ == "__main__":
    port = int(sys.argv[1])
    socketio.run(app, allow_unsafe_werkzeug=True, port=port)