from __future__ import annotations
import json
from multiprocessing import Queue
from typing import TYPE_CHECKING

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

if TYPE_CHECKING:
    from fibers.gui.forest_connector.forest_connector import TreeData
from forest import build_dir, asset_dir
from flask_cors import CORS
import sys
from time import sleep

chattingLock = False
#TODO: if only one user, chattingLock should be fine to avoid the message being sent when the previous chat hasn't completed yet.
# in more complicated use case, maybe we need a queue to handle the chattingLock (probably socket?) or a database to store the chattingLock status.


class ServerData:
    def __init__(self):
        self.tree = {}
        self.tree_id = None
        self.trees = {}

def patch_tree(currTree: TreeData, patchTree: TreeData):
    if currTree is None:
        currTree = {
            "selectedNode": None,
            "nodeDict": {}
        }
    if patchTree["selectedNode"] is not None:
        currTree["selectedNode"] = patchTree["selectedNode"]
    if patchTree["nodeDict"] is not None:
        for key in patchTree["nodeDict"]:
            new_node = patchTree["nodeDict"][key]
            if new_node is None:
                if key in currTree["nodeDict"]:
                    del currTree["nodeDict"][key]
            else:
                if "nodeDict" not in currTree:
                    currTree["nodeDict"] = {}
                currTree["nodeDict"][key] = new_node
    return currTree

def main(port, message_to_main: Queue):
    app = Flask(__name__, template_folder=build_dir, static_folder=asset_dir,
                static_url_path='/assets')
    CORS(app)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, cors_allowed_origins="*")

    data = ServerData()

    import logging

    log = logging.getLogger('werkzeug')
    log.disabled = True
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None



    @socketio.on('connect')
    def handle_connect():
        emit('Connected!')

    @socketio.on('requestTrees')
    def requestTree():
        emit('setTrees', data.trees)

    @socketio.on('message_to_main')
    def recv_message_to_main(data):
        # get the attached message and put it into the message_to_main queue.
        message_to_main.put(data)


    @app.route('/visualization')
    def visualization():
        return render_template('index.html')


    # update tree
    @app.route('/updateTree', methods=['PUT'])
    def updateTree():
        # TODO: check if the tree is valid.
        tree_patch = request.get_json()['tree']
        data.tree = patch_tree(data.tree, tree_patch)
        data.tree_id = request.get_json()['tree_id']
        data.trees[data.tree_id] = data.tree
        # TODO: check if the tree_id is valid.
        socketio.emit('patchTree', {"tree": tree_patch, "tree_id": data.tree_id})
        return "OK"


    # ChatBot interaction.
    # Currently only support GPT.
    @app.route('/chatFocusNode', methods=['POST'])
    def chatFocusNode():
        global chattingLock
        # data.tree_id = request.get_json()['tree_id']
        # data.tree = data.trees[data.tree_id]
        # socketio.emit('setTree', {"tree": data.tree, "tree_id": data.tree_id})
        try:
            if chattingLock:
                return json.dumps({"message": "Chatting is locked. Please wait for the previous chat to complete.", "status": 400})
            else:
                chattingLock = True
                sleep(3)
                # TODO: handle input (contexts? history?) and call external APIs.
                chattingLock = False
                return json.dumps(
                    {"message": "Hello", "status": 200})
        except Exception as e:
            chattingLock = False
            return json.dumps({"message": str(e), "status": 500})


    socketio.run(app, allow_unsafe_werkzeug=True, port=port)


if __name__ == '__main__':
    port = int(sys.argv[1])
    main(port, Queue())