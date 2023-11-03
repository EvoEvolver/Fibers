from __future__ import annotations

from json import JSONEncoder

from fibers.tree import Node, Tree


class FibersEncoder(JSONEncoder):
    def default(self, o):
        #if isinstance(o, Node):
        #    return serialize_node(o)
        #elif isinstance(o, Tree):
        #    return serialize_tree(o)
        #else:
        raise TypeError(f'Object of type {o.__class__.__name__} '
                        f'is not JSON serializable')

def serialize_node(node: Node):
    node_class_data = {}
    for node_class in node.node_classes:
        data = node_class.serialize(node)
        if data is not None:
            node_class_data[node_class.__name__] = data

    return {
        "path": node.path(),
        "content": node.content,
        "node_class_data": node_class_data
    }

def serialize_tree(tree: Tree):
    res = []
    for node in tree.all_nodes():
        res.append(serialize_node(node))
    return res