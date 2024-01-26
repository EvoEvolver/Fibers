from __future__ import annotations

import time
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection

import webbrowser

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading

import os

from forest import build_dir, asset_dir, lazy_build, build
import sys

class ForestServer:
    def __init__(self, fibers_conn: Connection):
        lazy_build()
        self.app = Flask(__name__, template_folder=build_dir, static_folder=asset_dir, static_url_path='/assets')
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        # check if mode exists in environment variable, and check if it is dev if present.
        self.in_dev_mode = (os.getenv("mode") is not None and os.getenv("mode") == "dev")
        self.port = 30000 + os.getpid() % 10000 if not self.in_dev_mode else 29999

        self.connected = False

        self.fibers_conn = fibers_conn
        # to hide warnings from flask.
        import logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

    def run(self):
        @self.socketio.on('connect')
        def handle_connect():
            emit('Connected!')
            self.connected = True

        @self.socketio.on('requestTree')
        def requestTree():
            pass
            #emit('setTree', self.tree)

        @self.app.route('/visualization')
        def visualization():
            return render_template('index.html')

        @self.app.route('/stop')
        def stop():
            self.socketio.stop()

        def run_socketio():
            self.socketio.run(self.app, allow_unsafe_werkzeug=True, port=self.port)

        socketio_thread = threading.Thread(target=run_socketio)
        socketio_thread.start()

        url = f"http://127.0.0.1:{self.port}/visualization"
        # Open the URL in the default web browser
        if not self.in_dev_mode: webbrowser.open(url)

        while not self.connected:
            time.sleep(0.1)

        print("Running on", url)
        self.fibers_conn.send(("connected", None))

        while True:
            try:
                msg, data = self.fibers_conn.recv()
                if msg == "stop":
                    stop()
                elif msg == "update_tree":
                    self.update_tree(data)
            except EOFError:
                break


    def update_tree(self, tree_json):
        self.socketio.emit('setTree', tree_json)



def run_server(fibers_conn: Connection):
    server = ForestServer(fibers_conn)
    server.run()



class ForestConnector:
    """
    The connector to connect to the Forest visualization.
    Flask and socket will be running to exchange information between.
    """

    def __init__(self):
        self.forest_conn: Connection = None
        self.forest_server_process: Process = None

    def run(self):
        fibers_end, forest_end = Pipe()
        p = Process(target=run_server, args=((forest_end,)))
        self.forest_server_process = p
        p.start()
        self.forest_conn = fibers_end
        if self.forest_conn.poll(1):
            msg, data = self.forest_conn.recv()
            assert msg == "connected"
        else:
            print("Forest visualization server not responding.")

    def update_tree(self, tree_json):
        self.forest_conn.send(("update_tree", tree_json))

    def stop(self):
        self.forest_server_process.terminate()



class ForestConnected:
    pass


if __name__ == '__main__':
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    tree.show_tree_gui_react()

