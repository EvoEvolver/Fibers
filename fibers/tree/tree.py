from __future__ import annotations

import time
from typing import Dict, List, Callable, Tuple
import dill
from bidict import bidict

from fibers.tree.node import Node, ContentMap
from fibers.gui.forest_connector.forest_connector import ForestConnector, ForestConnected
from fibers.gui.renderer import Renderer

class Tree:
    """
    Store the information of nodes contained
    The information is mainly the path and children of each node
    """
    tree_id = 0
    forest_connector = None
    def __init__(self, root_content=""):
        """
        :param root_content: The content of the root of the tree
        """
        self.children: Dict[Node, Dict[str, Node]] = {}
        self.node_path: bidict[Node, Tuple[str, ...]] = bidict()

        # Set up the root
        root = Node(self)
        self.children[root]: Dict[Node, Node] = {}
        self.node_path[root]: Dict[Node, Tuple[str, ...]] = tuple()
        root.set_content(root_content)

        self.class_data = {}
        self.tree_id = Tree.tree_id
        Tree.tree_id += 1

    """
    ## Node information query
    """

    def get_node_path(self, node: Node) -> Tuple[str, ...]:
        try:
            return self.node_path[node]
        except KeyError:
            raise Exception(f"Node {node.node_id} not in tree")

    def get_children_dict(self, node: Node) -> Dict[str, Node]:
        return self.children[node]

    def get_parent(self, node: Node) -> Node | None:
        node_path = self.get_node_path(node)
        if len(node_path) == 0:
            return None
        parent_path = node_path[:-1]
        parent = self.get_node_by_path(parent_path)
        return parent

    def has_child(self, node: Node, key: str) -> bool:
        return key in self.get_children_dict(node)

    def has_node(self, node: Node) -> bool:
        return node in self.node_path

    def all_nodes(self):
        return list(self.children.keys())

    @property
    def root(self) -> Node:
        root = self.get_node_by_path(tuple())
        return root

    @property
    def topic(self) -> str:
        return self.root.content

    """
    ## Node operations
    """

    def set_root(self, node: Node):
        if self.root in self.children:
            children = self.children[self.root]
            del self.children[self.root]
        else:
            children = {}
        self.children[node] = children
        del self.node_path[self.root]
        self.node_path[node] = tuple()

    def get_node_by_path(self, path: Tuple | List) -> Node | None:
        path = tuple(path)
        try:
            return self.node_path.inverse[path]
        except KeyError:
            return None

    def add_node_by_path(self, path: Tuple[str] | List[str], node: Node | str) -> Node:
        if isinstance(node, str):
            node_content = node
            node = Node(self)
            node.set_content(node_content)
        node: Node
        if len(path) == 0:
            self.set_root(node)
            return node
        leaf = self.root
        for key in path[:-1]:
            children = self.children[leaf]
            if key not in children:
                self.add_child(key, leaf, Node(self))
            leaf = children[key]
        self.add_child(path[-1], leaf, node)
        return node

    def new_node_by_path(self, path: List[str]) -> Node:
        new_node = Node(self)
        self.add_node_by_path(path, new_node)
        return new_node

    def add_child(self, key: str, parent: Node, child: Node):
        if child.tree is not self:
            child = child.copy_to(self)
        if child not in self.children:
            self.children[child] = {}
        # ensure the parent is in the tree
        assert self.has_node(parent)
        parent_node_path = self.get_node_path(parent)
        children_dict = self.get_children_dict(parent)

        if key in children_dict:
            old_child = children_dict[key]
            del self.children[old_child]
            del self.node_path[old_child]

        children_dict[key] = child
        child_node_path = parent_node_path + (key,)
        self.node_path[child] = child_node_path

    def remove_node(self, node: Node):
        """
        Remove a node from the tree
        It is better to create another tree that removing a node
        :param node:
        :return:
        """
        descendants = list(node.iter_subtree_with_dfs())[:-1]
        for descendant in descendants:
            del self.node_path[descendant]
            del self.children[descendant]

        parent = self.get_parent(node)
        children_dict = self.get_children_dict(parent)
        for key, child in children_dict.items():
            if child is node:
                del children_dict[key]
                break

        del self.children[node]
        del self.node_path[node]

    """
    ## Sub-tree extraction
    """

    def duplicate_tree_by_node_mapping(self, node_mapping: Callable[
        [Node, Tree], Node]) -> Tree:
        """
        Duplicate the tree by mapping each node to a new node
        It can also be used for creating a copy of the tree
        :param node_mapping: The mapping function for each node
        :return: A new tree
        """
        new_tree = Tree(self.topic)
        for node in self.all_nodes():
            new_path = self.get_node_path(node)
            new_tree.add_node_by_path(new_path, node_mapping(node, new_tree))
        return new_tree

    @staticmethod
    def from_nodes(nodes: List[Node]) -> Tree:
        new_tree = Tree()
        for node in nodes:
            new_tree.add_node_by_path(node.path(), node)
        return new_tree

    """
    ## Iterators
    """

    def iter_with_bfs(self):
        """
        Iterate the tree with depth first search
        Output the shallowest nodes first
        :return: the iterator
        """
        return self.root.iter_subtree_with_bfs()

    def iter_with_dfs(self):
        """
        Iterate the tree with depth first search
        Output the deepest nodes first
        :return: the iterator
        """
        return self.root.iter_subtree_with_dfs()

    """
    ## Persistence of the tree
    """

    def save(self, path: str):
        # TODO: We need to test this function and make sure it works
        with open(path, "wb") as f:
            try:
                dill.dump(self, f)
            except Exception as e:
                print(e)

    @staticmethod
    def load(path: str) -> Tree:
        # TODO: We need to test this function and make sure it works
        with open(path, "rb") as f:
            tree = dill.load(f)
        return tree

    def __repr__(self):
        return f"<{self.__class__.__name__}> {self.root.content!r}"

    """
       ## Visualization of tree
       """

    def show_tree_gui_old(self):
        """
        Show the tree in a webpage
        """
        from fibers.gui.tree import draw_treemap
        draw_treemap(self.root)


    def show_tree_gui_react(self, renderer=None, dev_mode=False):
        """
        Show the tree in a webpage
        """
        if renderer is None:
            renderer = Renderer

        tree_json = renderer().render_to_json(self.root)
        if Tree.forest_connector is None:
            Tree.forest_connector = ForestConnector(dev_mode=dev_mode)
            Tree.forest_connector.run()
        Tree.forest_connector.update_tree(tree_json, self.tree_id)


    def stop_tree_gui_react(self):
        Tree.forest_connector.stop()

    def show_interactive_gui(self, renderer):
        pass