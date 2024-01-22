import inspect

import fibers
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.tree.node import ContentMap, Node
from fibers.tree.node_class.code_node import get_obj, get_docs


def ncol_map(n: Node):
    try:
        obj = get_obj(n)
        src = inspect.getsource(obj)
        length = len(src.split("\n"))
        return f"(ncol: {length})" + (get_docs(n) or n.content)
    except:
        try:
            return get_docs(n) or ""
        except:
            return n.content


content_map = ContentMap(
    content_map=ncol_map,
)

tree = get_tree_for_module(fibers)
tree.show_tree_gui(content_map)
tree.show_tree_gui_react()