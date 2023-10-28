from fibers.data_loader.module_to_tree import get_tree_for_module



if __name__ == "__main__":
    from fibers import transform
    tree = get_tree_for_module(transform)
    tree.show_tree_gui()
