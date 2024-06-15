from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import Attr

if TYPE_CHECKING:
    from fibers.tree import Node


class Citing(Attr):
    def __init__(self, node):
        super().__init__(node)
        self.citing_nodes: List[Node] = []

    def add_citation(self, node: Node):
        self.citing_nodes.append(node)

    def render(self, rendered):
        if len(self.citing_nodes) > 0:
            rendered.tabs["citing"] = "<br/>".join([node.title for node in self.citing_nodes])