from __future__ import annotations
from typing import TYPE_CHECKING, Dict



if TYPE_CHECKING:
    from fibers.tree import Node
    from fibers.gui.renderer import Rendered


class NodeClass:

    @classmethod
    def set_attr(cls, node: Node, attr_name: str, attr_value):
        node.add_class(cls)
        node.class_data[cls][attr_name] = attr_value

    @classmethod
    def get_attr(cls, node: Node, attr_name: str):
        return node.class_data[cls].get(attr_name, None)

    @classmethod
    def get_data(cls, node: Node) -> Dict:
        return node.class_data[cls]

    @classmethod
    def render(cls, node: Node, rendered: Rendered):
        pass