from __future__ import annotations

from typing import Dict, List, Callable, Tuple, TYPE_CHECKING

import webbrowser

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading

import os

from forest import build_dir, asset_dir, lazy_build, build
import sys

DEFAULT_PORT = 29999
class ForestConnector:
    """
    The connector to connect to the Forest visualization.
    Flask and socket will be running to exchange information between.
    """

    def __init__(self, tree = None):
        lazy_build()
        self.app = Flask(__name__, template_folder=build_dir, static_folder=asset_dir, static_url_path='/assets')
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.tree = tree
        self.port = DEFAULT_PORT
        # to hide warnings from flask.
        import logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None
        if tree is not None:
            # An initial tree is given.
            self.tree = tree

    def update_tree(self, tree):
        self.tree = tree
        self.socketio.emit('setTree', self.tree)

    def run(self):
        socketio_thread = None
        @self.socketio.on('connect')
        def handle_connect():
            emit('Connected!')

        @self.socketio.on('requestTree')
        def requestTree():
            emit('setTree', self.tree)

        @self.app.route('/visualization')
        def visualization():
            return render_template('index.html')


        # check if mode exists in environment variable, and check if it is dev if present.
        dev_mode = (os.getenv("mode") is not None and os.getenv("mode") == "dev")
        self.port = 30000 + os.getpid() % 10000 if not dev_mode else 29999

        def run_socketio():
            self.socketio.run(self.app, allow_unsafe_werkzeug=True, port=self.port)

        socketio_thread = threading.Thread(target=run_socketio)
        socketio_thread.start()


        url = f"http://127.0.0.1:{self.port}/visualization"

        # Open the URL in the default web browser
        if not dev_mode: webbrowser.open(url)


class ForestConnected:
    pass