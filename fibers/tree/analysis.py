from fibers.tree import Tree


def analyze_tree_sparsity(tree: Tree):
    """
    Return the average number of children per node.
    """
    nodes = tree.all_nodes()
    max_children = -1
    total_children = 0
    n_non_leaf_nodes = 0
    for node in nodes:
        n_children = len(node.children())
        if n_children > 0:
            n_non_leaf_nodes += 1
            total_children += n_children
        max_children = max(max_children, n_children)
    average_children = total_children / n_non_leaf_nodes
    heavy_nodes = get_children_heavy_nodes(tree)
    print("Total_nodes:", len(nodes))
    print("Average children per non-leaf node:", average_children)
    print("Max children per node:", max_children)
    # print heavy nodes
    for node in heavy_nodes:
        print("Node:", node.path())
        print("Children:", len(node.children()))
        print("Content:", node.content)
        print("")

def get_children_heavy_nodes(tree: Tree, min_children=8):
    """
    Return a list of nodes with at least min_children children.
    """
    nodes = tree.all_nodes()
    heavy_nodes = []
    for node in nodes:
        n_children = len(node.children())
        if n_children >= min_children:
            heavy_nodes.append(node)
    return heavy_nodes