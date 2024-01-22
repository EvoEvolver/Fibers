from __future__ import annotations

import inspect
from textwrap import dedent

from fibers.tree.node_class.code_node import set_code_obj
from moduler.core import build_module_tree
from moduler import Struct

from fibers.data_loader.markdown_to_tree import markdown_to_tree
from fibers.tree import Node, Tree

from fibers.tree.node_class import CodeNodeClass

"""
This modules is for extract the information from python modules and build a tree for it.


## Get tree for module

"""


def get_tree_for_module(module):
    module_name = module.__name__
    tree = Tree(
        "Tree of module: " + module_name)
    module_struct = build_module_tree(module)
    build_tree_for_struct(module_struct, tree.root)
    return tree


def build_tree_for_struct(curr_struct: Struct, root_note: Node) -> Node:
    """
    :param curr_struct: The struct to be added to the child of the root_note
    :param root_note: The root note to be filled with children from curr_struct
    :return: the node constructed from curr_struct
    """
    curr_key = curr_struct.name
    curr_node = root_note.new_child(curr_key)
    set_code_obj(curr_node, curr_struct.struct_type, curr_struct.obj)

    for child_struct in curr_struct.children:
        match child_struct.struct_type:
            case "function":
                build_tree_for_struct(child_struct, curr_node)
            case "module":
                build_tree_for_struct(child_struct, curr_node)
            case "class":
                build_tree_for_struct(child_struct, curr_node)
            case "comment":
                # Add the comment to the content of the current node
                curr_node.be(curr_node.content + "\n" + child_struct.obj)
            case "section":
                build_tree_for_struct(child_struct, curr_node)
            case "todo":
                build_tree_for_struct(child_struct, curr_node)
            case "example":
                build_tree_for_struct(child_struct, curr_node)
            case "document":
                markdown_src = child_struct.obj
                readme_tree = markdown_to_tree(markdown_src, title="README")
                curr_node.attach_tree(readme_tree)
                new_node = curr_node.s("README")
                set_code_obj(new_node, "document",
                                           child_struct.obj)
            case _:
                raise ValueError("Unknown struct type: " + child_struct.struct_type)
    return curr_node


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
