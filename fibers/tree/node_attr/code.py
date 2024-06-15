from __future__ import annotations

import html
import inspect
from typing import TYPE_CHECKING, Any

from .base import Attr

if TYPE_CHECKING:
    from fibers.tree import Node

class CodeData(Attr):
    def __init__(self, node: Node):
        super().__init__(node)
        self.obj_type = None
        self.obj = None

    def render(self, rendered):
        content = []
        if get_type(self.node) in ["function", "example"]:
            content.append(f"""
        <Code
        code="{html.escape(get_source(self.node))}"
        """ + f"""
        language="python"
        />
        
        """)
        content.append(f"Type: {get_type(self.node)}")

        del rendered.tabs["content"]
        rendered.tabs["code"] = "<br/>".join(content)



def set_code_obj(node: Node, type_name: str, obj: Any):
    assert type_name in ["function", "class", "module", "document", "section", "todo", "example"]
    code_data = CodeData(node)
    code_data.obj_type = type_name
    code_data.obj = obj

def get_type(node: Node):
    return node.get_attr(CodeData).obj_type

def get_obj(node: Node) -> object:
    return node.get_attr(CodeData).obj

def get_docs(node: Node):
    raise NotImplementedError


def get_source(node: Node):
    obj = get_obj(node)
    # get source by inspect
    return inspect.getsource(obj)