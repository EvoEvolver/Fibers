from __future__ import annotations

from typing import Dict, List, Callable, Tuple, TYPE_CHECKING

import webbrowser

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading

import os

from fibers.tree.node_class import NodeClass


current_file_directory = os.path.dirname(os.path.abspath(__file__))
project_root = current_file_directory
while not os.path.isfile(os.path.join(project_root, 'pyproject.toml')):
    project_root = os.path.dirname(project_root)

parent_directory = os.path.dirname(project_root)
template_dir = os.path.join(parent_directory, 'Forest/dist')
static_dir = os.path.join(template_dir, 'assets')  # Path to the assets directory




class ForestConnector:
    """
    The connector to connect to the Forest visualization.
    Flask and socket will be running to exchange information between.
    """

    def __init__(self, tree = None):
        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/assets')
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.tree = tree
        if tree is not None:
            # An initial tree is given.
            self.update_tree(tree)

    def update_tree(self, tree):
        self.tree = tree
        self.socketio.emit('tree', self.tree)

    def run(self):
        @self.socketio.on('connect')
        def handle_connect():

            emit('Connected!')

        @self.socketio.on('requestTree')
        def requestTree():
            print("Frontend is requesting a tree")
            emit('tree', self.tree)


        @self.app.route('/visualization')
        def visualization():
            return render_template('index.html')

        def run_socketio():
            self.socketio.run(self.app, allow_unsafe_werkzeug=True)

        socketio_thread = threading.Thread(target=run_socketio)
        socketio_thread.start()


        url = "http://127.0.0.1:5000/visualization"

        # Open the URL in the default web browser
        webbrowser.open(url)


class ForestConnected:
    pass