import inspect
from functools import wraps
from textwrap import dedent, indent

from fibers.tree import Node
from fibers.tree.node_attr.code import get_type


def get_function_header(function):
    res = ["def", " "]
    # Get the function signature
    signature = inspect.signature(function)
    # Print the function signature
    res.append(function.__name__)
    res.append(str(signature))
    res.append(":\n")
    # Get the function docstring
    docstring = function.__doc__
    if docstring is None:
        docstring = ""
    docstring = dedent(docstring)
    docstring = indent(docstring, "    ")
    if docstring is not None:
        res.append("    \"\"\"")
        res.append(docstring)
        res.append("    \"\"\"\n")
    return "".join(res)


if __name__ == '__main__':
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper

    @decorator
    def my_function(param1: int, param2: str = "123") -> float:
        """
        This is a function
        :param param1: some words
        :param param2: some words
        :return:
        """
        # function body
        pass

    # Print the function signature
    print(get_function_header(my_function))


def get_function_module_env(function_node: Node):
    """
    Get the environment of the function, including the module, class, and section that the function is in.
    Stop when the first module ancestor is reached.
    :param function_node: The node of the function
    :return: Lines of text, in which each line is a name of an ancestor node
    """
    ancestor_nodes = [function_node.parent]
    while True:
        last_parent = ancestor_nodes[-1]
        last_parent_parent = last_parent.parent
        if last_parent_parent.parent is None:
            break
        ancestor_nodes.append(last_parent_parent)
        if get_type(last_parent) == "module":
            break

    parent_nodes = ancestor_nodes[::-1]
    res = []
    if len(parent_nodes) == 0:
        return "The node is root"

    for i, node in enumerate(parent_nodes):
        res.append(">" * i + get_type(node) + ":" + node.title)
    return "\n".join(res)
