from __future__ import annotations
from typing import TYPE_CHECKING, Any

from fibers.tree.node_class.abstract_node import NodeClass

if TYPE_CHECKING:
    from fibers.tree import Node

class CodeNodeClass(NodeClass):
    @staticmethod
    def set_type_obj(node: Node, type_name: str, obj: Any):
        assert type_name in ["function", "class", "module", "document", "section", "todo", "example"]
        node.add_class(CodeNodeClass)
        CodeNodeClass.set_attr(node, "module_tree_type", type_name)
        CodeNodeClass.set_attr(node, "module_tree_obj", obj)

    @staticmethod
    def get_type(node: Node):
        return CodeNodeClass.get_attr(node, "module_tree_type")

    @staticmethod
    def get_obj(node: Node):
        return CodeNodeClass.get_attr(node, "module_tree_obj")

    @staticmethod
    def serialize(node: Node):
        return CodeNodeClass.get_type(node)
