from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Dict, List, Type, Callable

from fibers.tree.node_class import NodeClass

if TYPE_CHECKING:
    from fibers.tree import Tree
    from fibers.tree.node_attr import Attr


class Node:
    """
    The class for node on the Tree class. It only stores the content of the node.
    The relation between nodes are stored in the Tree class instance (self.tree).
    """

    node_id = 0

    def __init__(self, tree: Tree):
        super().__init__()

        # content is string no matter what _content_type is
        self.content: str = ""
        # The root node helps merge two tree bases
        self.tree: Tree = tree
        # The class data is used to store the data of the node class
        self.class_data = {}

        self.attrs: Dict[Type[Attr], Attr] = {}
        # The node id is used to identify the node
        self.node_id = Node.node_id
        Node.node_id += 1

    def copy_to(self, tree: Tree):
        new_node = Node(tree)
        new_node.content = copy(self.content)
        new_node.class_data = copy(self.class_data)
        new_node.attrs = copy(self.attrs)
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

    def first_child(self) -> Node:
        for child in self.children().values():
            return child

    def title(self) -> str:
        node_path = self.path()
        if len(node_path) == 0:
            return ""
        return node_path[-1]

    def has_child(self, key: str = None):
        if key is None:
            return len(self.children()) > 0
        return self.tree.has_child(self, key)

    def is_empty(self):
        return len(self.content) == 0

    def sibling(self) -> Dict[str, Node] | None:
        """
        :return: the children dict of the parent node (i.e. the sibling dict of the node)
        """
        if self.parent() is None:
            return None
        return self.parent().children()

    def sibling_list(self) -> (List[Node], int):
        """
        :return: a tuple of (sibling_list, index of self in sibling_list)
        """
        self_sibling = self.sibling()
        if self_sibling is None:
            return [self], 0
        self_title = self.title()
        self_index = list(self_sibling.keys()).index(self_title)
        return list(self_sibling.values()), self_index

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

    def new_sibling_after(self, key: str) -> Node:
        self_path = list(self.path())
        new_path = self_path[:-1] + [key]
        try:
            existing_node = self.tree.get_node_by_path(new_path)
            new_path[-1] = new_path[-1] + " *"
        except:
            existing_node = None
        assert existing_node is None
        new_node = self.tree.new_node_by_path(self_path[:-1] + [key])
        parent_children = self.parent().children()
        new_children_dict = {}
        for title, node in list(parent_children.items())[:-1]:
            new_children_dict[title] = node
            if node is self:
                new_children_dict[key] = new_node
        self.tree.children[self.parent()] = new_children_dict
        return new_node

    def s(self, key) -> Node:
        """
        Creating a new child node or addressing an existing child node
        :param key: the key of the child node
        :return: the child node
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

    """
    ## Functions for setting content of node
    """

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

    """
    ## Function for change node's environment on its tree
    """

    def reset_path(self, new_path: List[str]):
        new_parent_path = tuple(new_path[:-1])
        if new_parent_path not in self.tree.node_path.inverse:
            parent = self.tree.new_node_by_path(new_parent_path)
        else:
            parent = self.tree.get_node_by_path(new_parent_path)
        old_parent = self.parent()
        if old_parent is not parent:
            old_parent_children = old_parent.children()
            del old_parent_children[self.title()]
        old_path = list(self.path())
        old_path_len = len(old_path)
        for child in self.iter_subtree_with_dfs():
            child_path = list(child.path())
            new_child_path = new_path + child_path[old_path_len:]
            del self.tree.node_path[child]
            self.tree.node_path[child] = tuple(new_child_path)
        self.tree.children[parent][new_path[-1]] = self
        self.tree.node_path[self] = tuple(new_path)


    def reset_title(self, title: str, overlap=False):
        new_path = list(self.path())
        old_title = new_path[-1]
        self_parent = self.parent()

        # Update the parent's children
        parent_children = self_parent.children()
        if title in parent_children:
            if not overlap:
                raise ValueError(f"Node with title {title} already exists")
            else:
                title = title + " (another)"

        new_parent_children = {}
        for key, node in parent_children.items():
            if node is self:
                new_parent_children[title] = self
            else:
                new_parent_children[key] = node
        self.tree.children[self_parent] = new_parent_children

        # Update the node path
        del self.tree.node_path[self]
        self.tree.node_path[self] = tuple(new_path)
        for node in self.iter_subtree_with_bfs():
            node._reset_path(len(new_path) - 1, title)

    def remove_self(self):
        self.tree.remove_node(self)

    def _reset_path(self, index, new_name):
        new_path = list(self.path())
        new_path[index] = new_name
        del self.tree.node_path[self]
        self.tree.node_path[self] = tuple(new_path)

    def attach_tree(self, tree: Tree):
        """
        Put the tree into the node
        :param tree: The tree to be attached as the descendant of the node
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

    """
    ## Magic functions
    """

    def __str__(self):
        if len(self.content) == 0:
            return "Path" + str(self.path())
        return self.content

    def __repr__(self):
        return f"<{self.__class__.__name__}> {str(self.path())}"

    def __hash__(self):
        return self.node_id

    def __eq__(self, other):
        return self.node_id == other.node_id

    """
    ## Node iterators
    """

    def iter_subtree_with_dfs(self):
        """
        Iterate the subtree with depth first search.
        Output the deepest nodes first.
        :return: An iterator of nodes
        """
        for child in self.children().values():
            yield from child.iter_subtree_with_dfs()
        yield self

    def iter_subtree_with_bfs(self):
        """
        Iterate the tree with breath first search.
        Output the shallowest nodes first.
        :return: An iterator of nodes
        """
        stack = []
        stack.append(self)
        while len(stack) > 0:
            curr_node = stack.pop(0)
            yield curr_node
            for child in curr_node.children().values():
                stack.append(child)

    """
    ## Node class related functions
    
    Node class is the class that process the node
    It represents the type of the node
    """

    def isinstance(self, node_class: Type[NodeClass]):
        return node_class in self.class_data.keys()

    def has_attr(self, attr_class: Type[Attr]):
        return attr_class in self.attrs.keys()

    def get_attr(self, attr_class: Type[Attr]):
        attr_value = self.get_attr_or_none(attr_class)
        if attr_value is None:
            return attr_class(self)
        return attr_value


    def get_attr_or_none(self, attr_class: Type[Attr]):
        return self.attrs.get(attr_class, None)

    def add_class(self, node_class: Type[NodeClass]):
        if self.isinstance(node_class):
            return
        if hasattr(node_class, "init_by"):
            init_by = node_class.init_by
        else:
            init_by = ""
        if init_by == "":
            self.class_data[node_class] = {}
        elif init_by == "obj":
            self.class_data[node_class] = node_class()

    def remove_class(self, node_class: Type[NodeClass]):
        if node_class in self.class_data.keys():
            del self.class_data[node_class]

    @property
    def node_classes(self):
        return list(self.class_data.keys())


class ContentMap:
    def __init__(self, content_map=None, title_map=None):
        self._content_map: Callable[
            [Node], str] = content_map if content_map is not None else lambda x: x.content
        self._title_map: Callable[
            [Node], str] = title_map if title_map is not None else lambda x: x.title()

    def get_title_and_content(self, node: Node):
        return self._title_map(node), self._content_map(node)


default_map = ContentMap()
