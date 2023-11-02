from __future__ import annotations

import inspect

from moduler.core import build_module_tree
from moduler import Struct

from fibers.data_loader.markdown_to_tree import markdown_to_tree
from fibers.tree import Node, Tree
from moduler.docs_parser import \
    parse_rst_docstring, \
    parse_google_docstring, Doc_parser

from fibers.tree.node_class import CodeNodeClass

"""
This modules is for extract the information from python modules and build a tree for it.


## Get tree for module

"""


def get_tree_for_module(module, docs_parser_type="rst"):
    if docs_parser_type == "rst":
        docs_parser = parse_rst_docstring
    elif docs_parser_type == "google":
        docs_parser = parse_google_docstring
    else:
        raise ValueError("docs_parser_type should be pycharm or vscode")
    module_name = module.__name__
    tree = Tree(
        "Tree of module: " + module_name)
    module_struct = build_module_tree(module)
    build_tree_for_struct(module_struct, tree.root, docs_parser)
    return tree


def build_tree_for_struct(curr_struct: Struct, root_note: Node,
                          docs_parser: Doc_parser) -> Node:
    """
    :param curr_struct: The struct to be added to the child of the root_note
    :param root_note: The root note to be filled with children from curr_struct
    :param docs_parser: The parser for the docstring
    :return: the node constructed from curr_struct
    """
    curr_key = curr_struct.name
    curr_node = root_note.new_child(curr_key)
    CodeNodeClass.set_type_obj(curr_node, curr_struct.struct_type, curr_struct.obj)

    for child_struct in curr_struct.children:
        new_node = None
        match child_struct.struct_type:
            case "function":
                new_node = process_function_struct(child_struct, curr_node, docs_parser)
            case "module":
                build_tree_for_struct(child_struct, curr_node, docs_parser)
            case "class":
                build_tree_for_struct(child_struct, curr_node, docs_parser)
            case "comment":
                curr_node.be(curr_node.content + "\n" + child_struct.obj)
            case "section":
                build_tree_for_struct(child_struct, curr_node, docs_parser)
            case "todo":
                build_tree_for_struct(child_struct, curr_node, docs_parser)
            case "example":
                build_tree_for_struct(child_struct, curr_node, docs_parser)
            case "document":
                markdown_src = child_struct.obj
                readme_tree = markdown_to_tree(markdown_src, title="README")
                curr_node.put_tree(readme_tree)
                new_node = curr_node.s("README")
            case _:
                raise ValueError("Unknown struct type: " + child_struct.struct_type)
        if new_node is not None:
            CodeNodeClass.set_type_obj(new_node, child_struct.struct_type, child_struct.obj)
    return curr_node


def process_function_struct(function_struct: Struct, parent_node: Node, docs_parser) -> Node:
    doc_raw = inspect.getdoc(function_struct.obj)
    if doc_raw is None:
        general, parameters, return_value = ("", {}, "")
    else:
        general, parameters, return_value = docs_parser(doc_raw)
    # Check if the function is callable
    if callable(function_struct.obj):
        parameters = {**get_empty_param_dict(function_struct.obj), **parameters}
    else:
        parameters = {**get_empty_param_dict(function_struct.obj.__func__), **parameters}
    if "self" in parameters:
        del parameters["self"]
    function_name = function_struct.name
    function_node = parent_node.s(function_name)
    function_node.be(general)
    return function_node

def get_empty_param_dict(func):
    param_dict = {}
    for param_name in inspect.signature(func).parameters.keys():
        param_dict[param_name] = ""
    return param_dict

def get_docs_in_prompt(doc_tuple):
    general, params, returns = doc_tuple
    if len(general) > 0:
        docs = general + "\n"
    else:
        docs = ""
    for param_name, param_doc in params.items():
        docs += "Parameter " + param_name + ": " + param_doc + "\n"
    if len(returns) > 0:
        docs += "Return value: " + returns + "\n"
    return docs


if __name__ == "__main__":
    from fibers.testing.testing_modules import v_lab

    tree = get_tree_for_module(v_lab)
    tree.show_tree_gui()
