from fibers.tree import Node
from fibers.tree.node_class import CodeNodeClass


def get_function_module_env(function_node: Node):
    """
    Get the environment of the function, including the module, class, and section that the function is in.
    Stop when the first module ancestor is reached.
    :param function_node: The node of the function
    :return: Lines of text, in which each line is a name of an ancestor node
    """
    parent_nodes = [function_node.parent()]
    while True:
        last_parent = parent_nodes[-1]
        parent_nodes.append(last_parent.parent())
        if CodeNodeClass.get_type(last_parent) == "module":
            break
    parent_nodes = parent_nodes[::-1]
    res = []
    for i, node in enumerate(parent_nodes):
        res.append(">" * i + CodeNodeClass.get_type(node) + ":" + node.title())
    return "\n".join(res)
