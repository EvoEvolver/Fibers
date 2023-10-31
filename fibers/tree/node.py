from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Dict, Any, List, Type, Set

from fibers.tree.node_class import TextNodeClass, NodeClass

if TYPE_CHECKING:
    from fibers.tree import Tree


class Node:
    """
    A tree-like data structure that stores tree
    usually for the direct summary of paragraphs

    The relation of the items are mainly represented by the tree structure
    It is like a book that AI can read

    Notice that Node object can be indexed by embedding vectors because its
    """

    def __init__(self, tree: Tree):
        super().__init__()

        # content is string no matter what _content_type is
        self.content: str = ""
        # The root node helps merge two tree bases
        self.tree: Tree = tree
        # The resource is the data that is indicated by the node
        self.resource: NodeResource = NodeResource()
        # The node class is the class that for processing the node
        self.node_classes: Set[Type[NodeClass]] = {TextNodeClass}

    def copy_to(self, tree: Tree):
        new_node = Node(tree)
        new_node.content = copy(self.content)
        new_node.resource = copy(self.resource)
        return new_node

    """
    ## Functions for getting the relation of nodes
    """

    def path(self):
        return self.tree.get_node_path(self)

    def parent(self):
        return self.tree.get_parent(self)

    def children(self) -> Dict[str, Node]:
        return self.tree.get_children_dict(self)

    def title(self) -> str:
        node_path = self.path()
        if len(node_path) == 0:
            return ""
        return node_path[-1]

    def has_child(self, key: str = None):
        if key is None:
            return len(self.children()) > 0
        return self.tree.has_child(self, key)

    @property
    def is_empty(self):
        return len(self.content) == 0

    @property
    def meta(self):
        return self.resource.meta

    def __getitem__(self, item):
        return self.resource.meta[item]

    def __setitem__(self, key, value):
        self.resource.meta[key] = value

    """
    ## Functions for adding children of node
    """

    def add_child(self, key: str, node) -> Node:
        self.tree.add_child(key, self, node)
        return node

    def new_child(self, key: str) -> Node:
        node = Node(self.tree)
        self.tree.add_child(key, self, node)
        return node

    """
    ## Functions for setting content of node
    """

    def s(self, key) -> Node:
        """
        Creating a new child node or addressing an existing child node
        :param key: the key of the child node
        :return:
        """
        tree = self.tree
        if isinstance(key, int) or isinstance(key, str):
            children = tree.get_children_dict(self)
            if key not in children:
                node = Node(tree)
                tree.add_child(key, self, node)
                return node
            return children[key]
        else:
            raise NotImplementedError()

    def set_content(self, content: str) -> Node:
        """
        :return: The node itself
        """
        self.content = content
        return self

    def be(self, content: str) -> Node:
        """
        :return: The node itself
        """
        self.content = content
        return self

    def remove_self(self):
        self.tree.remove_node(self)

    def reset_title(self, title: str, overlap=False):
        new_path = list(self.path())
        old_title = new_path[-1]

        # Update the parent's children
        parent_children = self.parent().children()
        if title in parent_children:
            if not overlap:
                raise ValueError(f"Node with title {title} already exists")
            else:
                title = title + " (another)"
        del parent_children[old_title]
        parent_children[title] = self

        # Update the node path
        del self.tree.node_path[self]
        self.tree.node_path[self] = tuple(new_path)
        for node in self.iter_subtree_with_bfs():
            node._reset_path(len(new_path)-1, title)

    def _reset_path(self, index, new_name):
        new_path = list(self.path())
        new_path[index] = new_name
        del self.tree.node_path[self]
        self.tree.node_path[self] = tuple(new_path)

    def put_tree(self, tree: Tree):
        """
        Put the tree into the node
        :param tree:
        :return:
        """
        self_path = self.path()
        self_tree = self.tree
        for node in tree.iter_with_bfs():
            node_path = node.path()
            if len(node_path) == 0:
                continue
            new_node = node.copy_to(self_tree)
            self_tree.add_node_by_path(self_path + node.path(), new_node)

    """
    ## Section for extract related nodes
    """

    def get_nodes_in_subtree(self) -> List[Node]:
        """
        Return all the nodes in the subtree
        """
        nodes = [self]
        for child in self.children().values():
            nodes += child.get_nodes_in_subtree()
        return nodes

    def __str__(self):
        if len(self.content) == 0:
            return "Path" + str(self.path())
        return self.content

    def __repr__(self):
        return f"<{self.__class__.__name__}> {str(self.path())}"

    """
    Node iterators
    """

    def iter_subtree_with_dfs(self):
        """
        Iterate the subtree with depth first search.
        Output the deepest nodes first.
        :return:
        """
        for child in self.children().values():
            yield from child.iter_subtree_with_dfs()
        yield self

    def iter_subtree_with_bfs(self):
        """
        Iterate the tree with breath first search.
        Output the shallowest nodes first.
        :return: the iterator
        """
        stack = []
        stack.append(self)
        while len(stack) > 0:
            curr_node = stack.pop(0)
            yield curr_node
            for child in curr_node.children().values():
                stack.append(child)

    """
    # Node class related functions
    Node class is the class that process the node
    It represents the type of the node
    """
    def isinstance(self, node_class: Type[NodeClass]):
        return node_class in self.node_classes

    def add_class(self, node_class: Type[NodeClass]):
        self.node_classes.add(node_class)


class NodeResource:
    def __init__(self):
        self.resource = {}
        # Possible types: Tree, Node, Function, Class, Module
        self.resource_type = {}
        # Metadata for storing information used by functions that process the node
        self.meta = {}

    def has_type(self, resource_type):
        return resource_type in self.resource_type.values()

    """
    ## Functions for getting resources
    """

    def get_resource_by_key(self, key):
        """
        Return the resource with the given key
        If the key does not exist, return None
        """
        return self.resource.get(key, None)

    def get_resource_by_type(self, resource_type):
        """
        Return the first resource of the given type
        """
        for key, value in self.resource_type.items():
            if value == resource_type:
                return self.resource[key]
        return None

    def get_resource_types(self):
        return set(self.resource_type.values())

    """
    ## Functions for adding resources
    """

    def add_resource(self, resource, resource_type: str, key: str):
        self.resource[key] = resource
        self.resource_type[key] = resource_type

    def add_text(self, text, key: str):
        self.add_resource(text, "text", key)

    def add_obj(self, text, key: str):
        self.add_resource(text, "obj", key)

    def add_tree(self, tree, key: str):
        self.add_resource(tree, "tree", key)

    def add_function(self, function, key: str):
        self.add_resource(function, "function", key)

    def add_module(self, module, key: str):
        self.add_resource(module, "module", key)

    def add_class(self, class_, key: str):
        self.add_resource(class_, "class", key)

    def add_node(self, node, key: str):
        self.add_resource(node, "node", key)
