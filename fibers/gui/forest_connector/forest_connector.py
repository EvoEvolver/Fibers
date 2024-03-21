from __future__ import annotations
import webbrowser
import os
from multiprocessing import Process

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

    def __init__(self, dev_mode=False):
        lazy_build()
        self.trees = {}
        self.port = 30000 + os.getpid() % 10000 if not dev_mode else 29999
        self.p = None
        self.dev_mode = dev_mode

    def update_tree(self, tree, tree_id):

        self.trees[tree_id] = tree
        url = f'http://127.0.0.1:{self.port}/updateTree'

        payload = json.dumps({
            "tree": tree,
            "tree_id": tree_id
        })
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"Updating tree {tree_id} to http://127.0.0.1:{self.port}/visualization")
        response = requests.request("PUT", url, headers=headers, data=payload)

    def run(self):
        # check if current process has finished its bootstrapping phase or not.
        # get project root.
        project_root = os.path.dirname(os.path.abspath(__file__))

        if is_port_in_use(self.port):
            # throw error
            raise Exception(f"Port {self.port} is not available.")
        # self.p = subprocess.Popen(['python3', f'{project_root}/server.py', str(self.port)])
        self.p = Process(target=main, args=(self.port,))
        self.p.start()
        #if not self.keep_alive_at_exit:
        atexit.register(cleanup_subprocess, self.p)

        # Wait for the server to start.
        url = f"http://127.0.0.1:{self.port}/visualization"

        initialization_success = False
        while not initialization_success or not is_port_in_use(self.port):
            try:
                initialization_success = True
            except Exception as e:
                print(e)
                time.sleep(0.1)
                continue

        # Open the URL in the default web browser
        if not self.dev_mode:
            webbrowser.open(url)

    def stop(self):
        try:
            # terminate the subprocess associated with this connector when this function is called.
            # TODO: check if the subprocess is still running.
            self.p.terminate()
            self.p.wait()  # Wait for the subprocess to complete after termination
            print("Subprocess terminated successfully!")

        except KeyboardInterrupt:
            # If the user presses Ctrl+C, terminate the subprocess
            self.p.terminate()
            self.p.wait()
            print("Subprocess terminated successfully!")

        finally:
            # Ensure the subprocess is terminated even if an exception occurs
            self.p.terminate()
            self.p.wait()


class ForestConnected:
    pass


node_connector_pool = {}