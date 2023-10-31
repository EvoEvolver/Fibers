from __future__ import annotations
from typing import TYPE_CHECKING

from fibers.tree.node_class.abstract_node import NodeClass

if TYPE_CHECKING:
    from fibers.tree import Node


class TextNodeClass(NodeClass):
    @staticmethod
    def get_n_words(node: Node):
        return len(node.content.split(" "))
