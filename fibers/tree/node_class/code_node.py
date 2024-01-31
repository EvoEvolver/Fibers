from __future__ import annotations

import html
import inspect
from typing import TYPE_CHECKING, Any

from fibers.tree.node_class.abstract_node import NodeClass

if TYPE_CHECKING:
    from fibers.tree import Node

class CodeNodeClass(NodeClass):
    @classmethod
    def render(cls, node: Node, rendered):
            if get_type(node) == "function":
                rendered.tabs["code"] = f"""
        <Code
        code="{html.escape(get_source(node))}"
        """ + """
        language="python"
        />
        """
            del rendered.tabs["content"]


def set_code_obj(node: Node, type_name: str, obj: Any):
    assert type_name in ["function", "class", "module", "document", "section", "todo", "example"]
    node.add_class(CodeNodeClass)
    CodeNodeClass.set_attr(node, "module_tree_type", type_name)
    CodeNodeClass.set_attr(node, "module_tree_obj", obj)

def get_type(node: Node):
    return CodeNodeClass.get_attr(node, "module_tree_type")
def get_obj(node: Node) -> object:
    return CodeNodeClass.get_attr(node, "module_tree_obj")
def get_docs(node: Node):
    assert False
    return CodeNodeClass.get_attr(node, "docs") or ""

def get_source(node: Node):
    obj = get_obj(node)
    # get source by inspect
    return inspect.getsource(obj)