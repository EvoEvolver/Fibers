import fibers
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.tree.node_attr.code_node import get_obj, get_source, get_type

if __name__ == '__main__':
    root = get_tree_for_module(fibers)
    for node in root.iter_subtree_with_dfs():
        print("---------------")
        print(get_obj(node))
        print(get_type(node))
