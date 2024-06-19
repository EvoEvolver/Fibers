from __future__ import annotations
import webbrowser
import os
from multiprocessing import Process
import multiprocessing as mp


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fibers.tree.node import Node

try:
    from fibers.gui.forest_connector.server import main
    from forest import lazy_build
except Exception as e:
    print(e)


import time
import requests
import json
import atexit

DEFAULT_PORT = 29999


def cleanup_subprocess(process):
    time.sleep(1.0)
    process.terminate()


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

class ForestConnector:
    """
    The connector to connect to the Forest visualization.
    Flask and socket will be running to exchange information between.
    """

    def __init__(self, dev_mode=False, interactive_mode=False):
        lazy_build()
        self.roots = {}
        self.backend_port = 30000 + os.getpid() % 10000 if not dev_mode else 29999
        self.frontend_port = self.backend_port if not dev_mode else 39999
        self.p = None
        self.dev_mode = dev_mode
        self.interactive_mode = interactive_mode or dev_mode
        os.environ['NO_PROXY'] = f'127.0.0.1'
        self.message_to_main = mp.Queue()

    def update_tree(self, tree_data, root_id):

        self.roots[root_id] = tree_data
        url = f'http://127.0.0.1:{self.backend_port}/updateTree'
        payload = json.dumps({
            "tree": tree_data,
            "tree_id": root_id
        })
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"Updating tree {root_id} to http://127.0.0.1:{self.frontend_port}/visualization")
        response = requests.request("PUT", url, headers=headers, data=payload)
        print("Updated tree")

    def run(self):
        # check if current process has finished its bootstrapping phase or not.
        # get project root.
        project_root = os.path.dirname(os.path.abspath(__file__))

        if is_port_in_use(self.backend_port):
            # throw error
            raise Exception(f"Port {self.backend_port} is not available.")
        # self.p = subprocess.Popen(['python3', f'{project_root}/server.py', str(self.port)])

        self.p = Process(target=main, args=(self.backend_port, self.message_to_main))
        self.p.start()
        #if not self.keep_alive_at_exit:
        atexit.register(cleanup_subprocess, self.p)

        # Wait for the server to start.
        url = f"http://127.0.0.1:{self.frontend_port}/visualization"

        initialization_success = False
        while not initialization_success or not is_port_in_use(self.backend_port):
            try:
                initialization_success = True
            except Exception as e:
                print(e)
                time.sleep(0.1)
                continue

        # Open the URL in the default web browser
        if not self.dev_mode:
            webbrowser.open(url)



    def process_message_from_frontend(self):
        # get information from the server by message_to_main
        while True:
            message = self.message_to_main.get()
            self.handle_message(message)

    def handle_message(self, message):
        from fibers.tree.node import All_Node
        target_node_id = message['node_id']
        node: Node = All_Node[target_node_id]
        for attr_class, attr_value in node.attrs.items():
            attr_value.handle_message(message)


class ForestConnected:
    pass


node_connector_pool = {}