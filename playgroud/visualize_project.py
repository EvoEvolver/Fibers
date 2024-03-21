import fibers
from fibers.data_loader.module_to_tree import get_tree_for_module

if __name__ == '__main__':
    tree = get_tree_for_module(fibers)
    tree.display()