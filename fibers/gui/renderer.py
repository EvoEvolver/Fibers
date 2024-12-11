from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fibers.tree import Node
    from fibers.gui.forest_connector.forest_connector import TreeData

class Rendered:
    def __init__(self, node):
        self.node: Node = node
        self.tabs = {}
        self.tools = [{},{}]
        self.children = []
        self.title = ""
        self.data = {}

    def to_json(self, node_dict):
        if self.node.node_id in node_dict:
            return
        node_json = self.to_json_without_children()
        # Add children
        for child in self.children:
            child.to_json(node_dict)
        node_dict[str(self.node.node_id)] = node_json

    def to_json_without_children(self) -> dict:
        children_ids = []
        for child in self.children:
            children_ids.append(str(child.node.node_id))
        parent_id = str(self.node._parent.node_id) if self.node._parent else None
        node_json = {
            "title": self.title,
            "tabs": self.tabs,
            "children": children_ids,
            "id": str(self.node.node_id),
            "parent": parent_id,
            "data": self.data,
            "tools": self.tools,
            "other_parents": [str(id) for id in self.node.parents[1:]]
        }
        return node_json


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
        self.render(node).to_json(node_dict)
        return {
            "selectedNode": str(node.node_id),
            "nodeDict": node_dict,
        }