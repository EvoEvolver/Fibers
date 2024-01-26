from __future__ import annotations
import webbrowser
import os
from forest import build_dir, asset_dir, lazy_build, build
import time
import requests
import json
import subprocess
import atexit

DEFAULT_PORT = 29999

def cleanup_subprocess(process):
    if process.poll() is None:
        process.terminate()
        process.wait()


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


class ForestConnector:
    """
    The connector to connect to the Forest visualization.
    Flask and socket will be running to exchange information between.
    """

    def __init__(self, tree = None):
        lazy_build()
        self.tree = tree
        self.port = DEFAULT_PORT
        self.p = None
        if tree is not None:
            # An initial tree is given.
            self.tree = tree

    def update_tree(self, tree):
        self.tree = tree
        url = f'http://127.0.0.1:{self.port}/updateTree'

        payload = json.dumps({
            "tree": tree
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("PUT", url, headers=headers, data=payload)

    def run(self):
        # check if mode exists in environment variable, and check if it is dev if present.
        dev_mode = (os.getenv("mode") is not None and os.getenv("mode") == "dev")
        self.port = 30000 + os.getpid() % 10000 if not dev_mode else 29999
        # check if current process has finished its bootstrapping phase or not.
        # get project root.
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        if is_port_in_use(self.port):
            # throw error
            raise Exception(f"Port {self.port} is not available.")
        self.p = subprocess.Popen(['python3', f'{project_root}/fibers/gui/forest_connector/server.py', str(self.port)])

        atexit.register(cleanup_subprocess, self.p)

        # Wait for the server to start.
        url = f"http://127.0.0.1:{self.port}/visualization"

        initialization_success = False
        while not initialization_success:
            try:
                self.update_tree(self.tree)
                initialization_success = True
            except:
                time.sleep(0.1)
                continue

        # Open the URL in the default web browser
        if not dev_mode:
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