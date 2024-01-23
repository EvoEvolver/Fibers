import inspect

import fibers
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.tree.node import ContentMap, Node
from fibers.tree.node_class.code_node import get_obj, get_docs, CodeNodeClass

tree = get_tree_for_module(fibers)
#tree.show_tree_gui(content_map)
tree.show_tree_gui_react([None, CodeNodeClass])