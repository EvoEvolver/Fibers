from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fibers.tree import Node
    from fibers.gui.forest_connector.forest_connector import TreeData

class Rendered:
    def __init__(self, node):
        self.node: Node = node
        self.tabs = {}
        self.tools = {}
        self.children = []
        self.title = ""

    def to_json(self, node_dict, parent_id) -> dict:
        node_json = self.to_json_without_children(parent_id)
        # Add children
        children_id = []
        for child in self.children:
            child.to_json(node_dict, str(self.node.node_id))
            children_id.append(str(child.node.node_id))
        node_json["children"] = children_id

        node_dict[str(self.node.node_id)] = node_json

    def to_json_without_children(self, parent_id) -> dict:
        return {
            "title": self.title,
            "tabs": self.tabs,
            "tools": self.tools,
            "children": None,
            "id": str(self.node.node_id),
            "parent": parent_id,
            "data": {},
        }


class Renderer:
    def __init__(self):
        pass

    def node_handler(self, node: Node, rendered: Rendered):
        for attr_class, attr_value in node.attrs.items():
            attr_value.render(rendered)

    def render(self, node: Node) -> Rendered:
        rendered = Rendered(node)
        rendered.title = node.title
        rendered.tabs["content"] = node.content
        self.node_handler(node, rendered)
        for child in node.children():
            rendered.children.append(self.render(child))
        return rendered

    def render_to_json(self, node: Node) -> TreeData:
        node_dict = {}
        self.render(node).to_json(node_dict, None)
        return {
            "selectedNode": str(node.node_id),
            "nodeDict": node_dict,
        }