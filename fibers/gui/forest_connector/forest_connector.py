from __future__ import annotations

import warnings
import webbrowser
import os
import multiprocessing as mp
from multiprocessing import Process

from typing import TYPE_CHECKING, Dict, TypedDict

import psutil

from fibers.gui.renderer import Renderer
from fibers.tree.node_attr.base import MessageResult
from nodejs import node as js_node

if TYPE_CHECKING:
    from fibers.tree.node import Node

try:
    from forest import lazy_build, server_dir
except Exception as e:
    print(e)


import time
import requests
import json
import atexit

class TreeData(TypedDict):
    selectedParent: str
    selectedNode: str
    nodeDict: Dict[str, dict]

DEFAULT_PORT = 29999

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def cleanup_subprocess(process):
    time.sleep(1.0)
    kill(process.pid)

def is_port_in_use(port: int, host: str) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def server_process(port, host, make_frontend):
    if make_frontend:
        return js_node.run([server_dir, '--BackendPort', str(port), "--Host", host])
    else:
        return js_node.run([server_dir, '--BackendPort', str(port), "--Host", host, "--NoFrontend"])

class ForestConnector:
    """
    The connector to connect to the Forest visualization.
    Flask and socket will be running to exchange information between.
    """

    def __init__(self, dev_mode=False, interactive_mode=False, host="127.0.0.1"):
        lazy_build()
        if ":" not in host:
            backend_port = 30000 + os.getpid() % 10000 if not dev_mode else 29999
        else:
            host, backend_port = host.split(":")
            backend_port = int(backend_port)
        self.backend_port = backend_port
        #self.frontend_port = self.backend_port if not dev_mode else 39999
        self.p = None
        self.host = host
        self.dev_mode = dev_mode
        self.interactive_mode = interactive_mode or dev_mode
        os.environ['NO_PROXY'] = f'127.0.0.1'
        self.message_to_main = mp.Queue()

    def update_tree(self, tree_data: TreeData, root_id):
        url = f'http://{self.host}:{self.backend_port}/updateTree'
        payload = json.dumps({
            "tree": tree_data,
            "tree_id": str(root_id)
        })
        headers = {
            'Content-Type': 'application/json'
        }
        print(f"Updating tree {root_id} to http://{self.host}:{self.backend_port}/")
        response = requests.request("PUT", url, headers=headers, data=payload)
        print("Updated tree")

    def run(self):
        if is_port_in_use(self.backend_port, self.host):
            # throw error
            if not self.dev_mode:
                raise Exception(f"Port {self.backend_port} is not available.")
            else:
                print(f"Port {self.backend_port} is not available. Assume the server is already running.")
                return


        if self.dev_mode:
            self.p = Process(target=server_process,
                             args=(self.backend_port, self.host, False))
        else:
            self.p = Process(target=server_process,
                             args=(self.backend_port, self.host, True))
        self.p.start()


        # Wait for the server to start.
        url = f"http://{self.host}:{self.backend_port}/"

        initialization_success = False
        while not initialization_success or not is_port_in_use(self.backend_port, self.host):
            try:
                initialization_success = True
            except Exception as e:
                print(e)
                time.sleep(0.1)
                continue

        # Open the URL in the default web browser
        if not self.dev_mode:
            try:
                pass
                webbrowser.open(url)
            except Exception as e:
                print(e)

        if self.interactive_mode or self.dev_mode:
            atexit.register(cleanup_subprocess, self.p)
        else:
            atexit.register(cleanup_subprocess, self.p)
            #cleanup_subprocess(self.p)
        return self.p


    def process_message_from_frontend(self):
        # get information from the server by message_to_main
        while True:
            message = self.message_to_main.get()
            try:
                self.handle_message(message)
            except Exception as e:
                warnings.warn(f"Error in handling message: {e}")
                print("Problematic message:", message)

    def handle_message(self, message):
        target_node_id = message['node_id']
        if target_node_id not in All_Node:
            return
        node: Node = All_Node[target_node_id]
        new_selected_node_id = None
        node_to_re_render = set()
        for attr_class, attr_value in node.attrs.items():
            res: MessageResult = attr_value.handle_message(message["message"])
            if res is None:
                continue
            node_to_re_render.update(res.node_to_re_render)
            if res.new_selected_node is not None:
                new_selected_node_id = res.new_selected_node.node_id
        node_dict = {}
        if len(node_to_re_render) == 0 and new_selected_node_id is None:
            return
        renderer = Renderer()
        for node in node_to_re_render:
            parent_id = str(node.parent.node_id) if node.parent is not None else None
            node_json = renderer.render(node).to_json_without_children(parent_id)
            node_dict[str(node.node_id)] = node_json
        tree_data = {
            "selectedNode": str(new_selected_node_id),
            "nodeDict": node_dict,
            "selectedParent": None
        }
        self.update_tree(tree_data, str(node.root().node_id))


node_connector_pool = {}