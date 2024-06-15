from __future__ import annotations

from typing import TYPE_CHECKING, Type, Callable, Dict

if TYPE_CHECKING:
    from fibers.tree import Node

class Rendered:
    def __init__(self):
        self.tabs = {}
        self.tools = {}
        self.children = []
        self.title = ""

    def to_json(self, parent_path: str = "") -> dict:
        children = []
        my_path = parent_path + "/" + self.title
        for child in self.children:
            children.append(child.to_json(my_path))
        return {
            "title": self.title,
            "tabs": self.tabs,
            "tools": self.tools,
            "children": children,
            "path": my_path,
            "data": {}
        }


class Renderer:
    def __init__(self):
        pass

    def node_handler(self, node: Node, rendered: Rendered):
        for attr_class, attr_value in node.attrs.items():
            attr_value.render(rendered)

    def render(self, node: Node) -> Rendered:
        rendered = Rendered()
        rendered.title = node.title
        rendered.tabs["content"] = node.content
        self.node_handler(node, rendered)
        for child in node.children():
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
