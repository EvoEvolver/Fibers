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