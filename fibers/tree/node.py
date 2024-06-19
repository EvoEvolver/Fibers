from __future__ import annotations

import uuid
from copy import copy
from typing import TYPE_CHECKING, Dict, List, Type

from fibers.gui.forest_connector import ForestConnector
from fibers.gui.forest_connector.forest_connector import node_connector_pool
from fibers.gui.renderer import Renderer

if TYPE_CHECKING:
    from fibers.tree.node_attr import Attr

All_Node = {}

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
        All_Node[str(self.node_id)] = self
        #
        self._children: List[Node] = []
        #
        self._parent: Node | None = None

    def copy_to(self):
        new_node = Node(self.title, self.content)
        new_node.attrs = copy(self.attrs)
        new_node._children = copy(self._children)
        new_node._parent = self._parent
        return new_node

    """
    ## Functions for getting the relation of nodes
    """

    def children(self) -> List[Node]:
        return self._children

    def parent(self) -> Node | None:
        return self._parent

    def first_child(self) -> Node | None:
        if len(self._children) > 0:
            return self._children[0]
        return None

    def has_child(self):
        return len(self.children()) > 0

    def is_empty(self):
        return len(self.content) == 0

    def sibling(self) -> List[Node] | None:
        """
        :return: the children dict of the parent node (i.e. the sibling dict of the node)
        """
        return self._parent.children()

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

    """
    ## Functions for adding children of node
    """

    def add_child(self, node: Node) -> Node:
        self._children.append(node)
        node._parent = self
        return node

    def new_child(self) -> Node:
        node = Node()
        self.add_child(node)
        return node

    def s(self, title: str, check_duplicate = True) -> Node:
        """
        :return: The new child node
        """
        if check_duplicate:
            for child in self.children():
                if child.title == title:
                    return child
        child = self.new_child()
        child.title = title
        return child

    def remove_child(self, node: Node):
        self._children.remove(node)
        node._parent = None

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
        self._parent.remove_child(self)

    def new_parent(self, parent: Node) -> Node:
        self.remove_self()
        parent.add_child(self)
        self._parent = parent
        return self

    """
    ## Section for extract related nodes
    """

    def get_nodes_in_subtree(self) -> List[Node]:
        """
        Return all the nodes in the subtree
        """
        nodes = [self]
        for child in self.children():
            nodes += child.get_nodes_in_subtree()
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
        for child in self.children():
            yield from child.iter_subtree_with_dfs()
        if not exclude_self:
            yield self

    def iter_subtree_with_bfs(self):
        """
        Iterate the tree with breath first search.
        Output the shallowest nodes first.
        :return: An iterator of nodes
        """
        stack = [self]
        while len(stack) > 0:
            curr_node = stack.pop(0)
            yield curr_node
            for child in curr_node.children():
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

    def display_whole_tree(self):
        self.root().display()

    def display(self, renderer=None, dev_mode=False, interactive=False):
        """
        Show the tree in a webpage
        """
        if self not in node_connector_pool.keys():
            forest_connector = ForestConnector(dev_mode=dev_mode, interactive_mode=interactive)
            node_connector_pool[Node] = forest_connector
            forest_connector.run()
        self.update_gui(renderer)
        if interactive or dev_mode:
            forest_connector.process_message_from_frontend()

    def update_gui(self, renderer=None):
        if renderer is None:
            renderer = Renderer
        tree_data = renderer().render_to_json(self)
        tree_data["selected"] = str(self.node_id)
        forest_connector = node_connector_pool.get(Node)
        if forest_connector is None:
            return
        else:
            forest_connector.update_tree(tree_data, self.node_id)
