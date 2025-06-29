from __future__ import annotations

import uuid
import webbrowser
from copy import copy
from typing import TYPE_CHECKING, Dict, List, Type, Set

import dill

from fibers.gui.forest_connector import ForestConnector
from fibers.gui.forest_connector.forest_connector import node_connector_pool
from fibers.gui.renderer import Renderer

if TYPE_CHECKING:
    from fibers.tree.node_attr import Attr


class Node:
    """
    The class for node on the Tree class. It only stores the content of the node.
    The relation between nodes are stored in the Tree class instance (self.tree).
    """

    def __init__(self, title="", content=""):
        super().__init__()

        # content is string no matter what _content_type is
        self.content: str = content
        #
        self.title: str = title
        # The attr data is used to store the data of the node
        self.attrs: Dict[Type[Attr], Attr] = {}
        # The node id is used to identify the node
        self.node_id = uuid.uuid4().int
        #
        self.children: List[Node] = []
        #
        self.parents: List[Node] = []
        #
        self.dirty = False

    def copy_to(self):
        new_node = Node(self.title, self.content)
        new_node.attrs = copy(self.attrs)
        new_node.children = copy(self._children)
        new_node.parents = copy(self.parents)
        return new_node

    def copy_whole_sub_tree(self):
        nodes = [node for node in self.iter_subtree_with_dfs()]
        node_map = {}
        for node in nodes:
            node_map[node] = Node(node.title, node.content)
        for node in nodes:
            new_node = node_map[node]
            for child in node.children:
                new_node._children.append(node_map[child])
            for parent in node.parents:
                if parent not in node_map:
                    continue
                new_node.parents.append(node_map[parent])
        return node_map

    def update_subtree_parents(self):
        nodes = [node for node in self.iter_subtree_with_dfs()]
        for node in nodes:
            node.parents = []
        for node in nodes:
            for child in node.children:
                if node not in child.parents:
                    child.parents.append(node)

    def update_subtree_children(self):
        nodes = [node for node in self.iter_subtree_with_dfs()]
        for node in nodes:
            node._children = []
        for node in nodes:
            for parent in node.parents:
                if node not in parent._children:
                    parent._children.append(node)


    """
    ## Functions for getting the relation of nodes
    """

    @property
    def _children(self):
        return self.children

    @_children.setter
    def _children(self, children):
        self.children = children

    def parent(self) -> Node | None:
        return self._parent

    @property
    def _parent(self):
        return self.parents[0] if len(self.parents) > 0 else None

    @_parent.setter
    def _parent(self, parent):
        if parent is None:
            self.parents = []
            return
        if parent in self.parents:
            self.parents.remove(parent)
        self.parents = [parent]+self.parents

    def first_child(self) -> Node | None:
        if len(self._children) > 0:
            return self._children[0]
        return None

    def has_child(self):
        return len(self.children) > 0

    def is_empty(self):
        return len(self.content) == 0

    def sibling(self) -> List[Node] | None:
        """
        :return: the children dict of the parent node (i.e. the sibling dict of the node)
        """
        return self._parent.children

    def index_in_siblings(self) -> int:
        return self.sibling().index(self)

    def root(self) -> Node:
        if self._parent is None:
            return self
        return self._parent.root()

    def path_to_root(self) -> List[Node]:
        ancestors = []
        curr_node = self
        while curr_node is not None:
            ancestors.append(curr_node)
            curr_node = curr_node._parent
        return ancestors

    def find_loop(self):
        node_on_path = []
        def dfs(node):
            if node in node_on_path:
                return node_on_path[node_on_path.index(node):]
            node_on_path.append(node)
            for child in node.children:
                loop = dfs(child)
                if loop is not None:
                    return loop
            node_on_path.remove(node)
            return None

        return dfs(self)

    def is_root(self):
        return len(self.parents) == 0


    """
    ## Functions for adding children of node
    """

    def add_child(self, node: Node) -> Node:
        self._children.append(node)
        node.parents.append(self)
        return node

    def new_child(self, title=None) -> Node:
        node = Node()
        self.add_child(node)
        if title is not None:
            node.title = title
        return node

    def s(self, title: str) -> Node:
        """
        :return: The new child node
        """
        child = self.new_child()
        child.title = title
        return child

    def remove_child(self, node: Node):
        try:
            self._children.remove(node)
        except ValueError:
            pass
        if self in node.parents:
            node.parents.remove(self)

    """
    ## Functions for setting content of node
    """

    def be(self, content: str) -> Node:
        """
        :return: The node itself
        """
        self.content = content
        return self

    """
    ## Function for change node's environment on its tree
    """

    def remove_self(self):
        for parent in self.parents:
            parent.remove_child(self)

    def change_parent(self, parent: Node) -> Node:
        self.remove_self()
        parent.add_child(self)
        self._parent = parent
        return self

    """
    ## Section for extract related nodes
    """

    def get_nodes_in_subtree(self) -> Set[Node]:
        """
        Return all the nodes in the subtree
        """
        nodes = list(self.iter_subtree_with_dfs())
        return nodes

    """
    ## Magic functions
    """

    def __str__(self):
        if len(self.content) == 0:
            return f"Node(title={str(self.title)})"
        return f"Node(content={str(self.content)})"

    def __repr__(self):
        return f"Node({str(self.title)})"

    def __hash__(self):
        return self.node_id

    def __eq__(self, other):
        return self.node_id == other.node_id

    """
    ## Node iterators
    """

    def iter_subtree_with_dfs(self, exclude_self=False):
        """
        Iterate the subtree with depth first search.
        Output the deepest nodes first.
        :return: An iterator of nodes
        """
        visited = set()
        for child in self.children:
            if child not in visited:
                visited.add(child)
                yield from child._iter_subtree_with_dfs(visited)
        if not exclude_self:
            yield self

    def _iter_subtree_with_dfs(self, visited: set):
        for child in self.children:
            if child not in visited:
                visited.add(child)
                yield from child.iter_subtree_with_dfs()
        yield self


    def iter_subtree_with_bfs(self, exclude_self=False):
        """
        Iterate the tree with breath first search.
        Output the shallowest nodes first.
        :return: An iterator of nodes
        """
        stack = [self]
        visited = set()
        visited.add(self)
        if not exclude_self:
            yield self
        while len(stack) > 0:
            curr_node = stack.pop(0)
            for child in curr_node.children:
                if child not in visited:
                    yield child
                    visited.add(child)
                    stack.append(child)



    """
    ## Node attrs related functions

    Node attrs stores the data of the node for different purposes.
    """

    def has_attr(self, attr_class: Type[Attr]):
        return attr_class in self.attrs.keys()

    def get_attr(self, attr_class: Type[Attr]):
        attr_value = self.get_attr_or_none(attr_class)
        if attr_value is None:
            return attr_class(self)
        return attr_value

    def get_attr_or_none(self, attr_class: Type[Attr]):
        return self.attrs.get(attr_class, None)

    """
    ## Visualization of tree
    """

    def display(self, renderer=None, dev_mode=False, interactive=False, host="127.0.0.1"):
        """
        Show the tree in a webpage
        """
        forest_process = None
        if self not in node_connector_pool.keys():
            forest_connector = ForestConnector(dev_mode=dev_mode, interactive_mode=interactive, host=host)
            node_connector_pool[Node] = forest_connector
            forest_process = forest_connector.run()
        else:
            forest_connector = node_connector_pool.get(Node)
        self.update_gui(renderer)
        # Open the URL in the default web browser
        url = f"http://{host}:{forest_connector.backend_port}/?id={self.node_id}"
        print(url)


    def update_gui(self, renderer=None):
        print("update gui")
        if renderer is None:
            renderer = Renderer
        tree_data = renderer().render_to_json(self)
        forest_connector = node_connector_pool.get(Node)
        print("finish update gui")
        if forest_connector is None:
            return
        else:
            print("try to update tree")
            forest_connector.update_tree(tree_data, self.node_id)
            print("finish update tree")

    """
    ## Persistence 
    """

    def save_sub_tree(self, path):
        node_dict = {}
        for node in self.iter_subtree_with_dfs():
            node_dict[node.node_id] = {
                "title": node.title,
                "content": node.content,
                "children": [child.node_id for child in node.children],
                "parents": [parent.node_id for parent in node.parents]
            }
        with open(path, "wb") as f:
            f.write(dill.dumps([node_dict, self.node_id]))


    @staticmethod
    def read_tree(path):
        with open(path, "rb") as f:
            node_dict, root_id = dill.loads(f.read())
        nodes = {}
        for node_id, node_data in node_dict.items():
            node = Node(node_data["title"], node_data["content"])
            node.node_id = node_id
            nodes[node_id] = node
        for node_id, node_data in node_dict.items():
            node = nodes[node_id]
            for child_id in node_data["children"]:
                node._children.append(nodes[child_id])
            for parent_id in node_data["parents"]:
                node.parents.append(nodes[parent_id])
        return nodes[root_id]

