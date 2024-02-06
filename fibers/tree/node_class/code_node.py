from __future__ import annotations

import html
import inspect
from typing import TYPE_CHECKING, Any

from fibers.tree.node_attr import Attr

if TYPE_CHECKING:
    from fibers.tree import Node

class CodeData(Attr):
    def __init__(self, node: Node):
        super().__init__(node)
        self.module_tree_type = None
        self.module_tree_obj = None

    @classmethod
    def render(cls, node: Node, rendered):
        content = []
        if get_type(node) in ["function", "example"]:
            content.append(f"""
        <Code
        code="{html.escape(get_source(node))}"
        """ + f"""
        language="python"
        />
        
        """)
        content.append(f"Type: {get_type(node)}")

        del rendered.tabs["content"]
        rendered.tabs["code"] = "<br/>".join(content)



def set_code_obj(node: Node, type_name: str, obj: Any):
    assert type_name in ["function", "class", "module", "document", "section", "todo", "example"]
    code_data = CodeData(node)
    code_data.module_tree_type = type_name
    code_data.module_tree_obj = obj

def get_type(node: Node):
    return node.get_attr(CodeData).module_tree_type

def get_obj(node: Node) -> object:
    return node.get_attr(CodeData).module_tree_obj

def get_docs(node: Node):
    raise NotImplementedError


def get_source(node: Node):
    obj = get_obj(node)
    # get source by inspect
    return inspect.getsource(obj)