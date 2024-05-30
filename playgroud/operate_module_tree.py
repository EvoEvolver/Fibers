import inspect

import fibers
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.tree.node_attr.code_node import get_obj, get_type
from fibers.utils.code_process import get_function_header

if __name__ == '__main__':
    root = get_tree_for_module(fibers)
    for node in root.iter_subtree_with_dfs():
        print("---------------")
        obj = get_obj(node)
        obj_type = get_type(node)
        print(obj_type)
        print(obj)
        if obj_type == "function":
            print(inspect.getsource(obj))