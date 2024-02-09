import fibers
from fibers.data_loader.module_to_tree import get_tree_for_module
import time

if __name__ == '__main__':
    tree = get_tree_for_module(fibers)
    tree.show_tree_gui_react()