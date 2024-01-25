from __future__ import annotations
from fibers.tree.node_class import CodeNodeClass
from fibers.tree.node_class.code_node import get_type, get_source
from typing import TYPE_CHECKING
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
        pass

    @classmethod
    def render(cls, node: Node) -> Rendered:
        rendered = Rendered()
        rendered.title = node.title()
        rendered.tabs["content"] = node.content
        if node.isinstance(CodeNodeClass):
            if get_type(node) == "function":
                rendered.tabs["code"] = get_source(node)
                del rendered.tabs["content"]

        for title, content in list(rendered.tabs.items()):
            if len(content.strip()) == 0:
                del rendered.tabs[title]
            else:
                rendered.tabs[title] = content.strip().replace("\n", "<br>")

        for title, child in node.children().items():
            rendered.children.append(cls.render(child))

        return rendered

    @classmethod
    def render_to_json(cls, node: Node) -> dict:
        return cls.render(node).to_json()

    @classmethod
    def render_to_json_old(cls, node: Node) -> dict:
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

        return new_to_old(cls.render(node).to_json())
