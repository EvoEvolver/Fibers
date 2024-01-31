from __future__ import annotations

import html

from fibers.tree.node_class import CodeNodeClass, NodeClass
from fibers.tree.node_class.code_node import get_type, get_source
from typing import TYPE_CHECKING, Type, Callable, Dict

if TYPE_CHECKING:
    from fibers.tree import Node

class Rendered:
    def __init__(self):
        self.tabs = {}
        self.tools = {}
        self.children = []
        self.title = ""

    def to_json(self):
        children = []
        for child in self.children:
            children.append(child.to_json())
        return {
            "title": self.title,
            "tabs": self.tabs,
            "tools": self.tools,
            "children": children,
            "data": {}
        }


class Renderer:
    def __init__(self):
        self.node_class_renderers: Dict[Type[NodeClass], Callable] = {
            CodeNodeClass: CodeNodeClass.render
        }

    """
    def add_default_class_render(self, node_class: Type[NodeClass]):
        self.node_class_renderers[node_class] = node_class.render

    def add_class_render(self, node_class: Type[NodeClass], render: Callable):
        self.node_class_renderers[node_class] = render

    """

    def node_handler(self, node, rendered: Rendered):
        for node_class in node.class_data:
            node_class.render(node, rendered)


    def render(self, node: Node) -> Rendered:
        rendered = Rendered()
        rendered.title = node.title()
        rendered.tabs["content"] = node.content
        self.node_handler(node, rendered)
        for title, child in node.children().items():
            rendered.children.append(self.render(child))
        return rendered

    def render_to_json(self, node: Node) -> dict:
        return self.render(node).to_json()

    def render_to_json_old(self, node: Node) -> dict:
        def new_to_old(new):
            new["id"] = new["title"]
            del new["tools"]
            tabs = list(new["tabs"].values())
            if len(tabs) > 0:
                new["content"] = tabs[0]
            else:
                new["content"] = ""
            new["sections"] = new["children"]
            del new["tabs"]
            del new["children"]
            for child in new["sections"]:
                new_to_old(child)
            return new

        return new_to_old(self.render(node).to_json())
