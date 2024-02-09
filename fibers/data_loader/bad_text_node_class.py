from fibers.tree import Node
from fibers.tree.node_attr import Attr


class BadTextNodeClass(Attr):
    def __init__(self, node):
        super().__init__(node)
        self.bad_reasons = set()

    @staticmethod
    def add_bad_reason(node, reason: str):
        add_bad_reason(node, reason)

    @staticmethod
    def remove_bad_reason(node, reason: str):
        remove_bad_reason(node, reason)

    @staticmethod
    def has_bad_reason(node, reason: str) -> bool:
        return has_bad_reason(node, reason)


def add_bad_reason(node: Node, reason: str):
    assert reason in ["overlap_to_sibling", "bad_title"]
    data = BadTextNodeClass.get(node)
    data.bad_reasons.add(reason)


def remove_bad_reason(node: Node, reason: str):
    data = BadTextNodeClass.get(node)
    if reason in data.bad_reasons:
        data.bad_reasons.remove(reason)
    if len(data.bad_reasons) == 0:
        del node.attrs[BadTextNodeClass]


def has_bad_reason(node: Node, reason: str) -> bool:
    if not node.has_attr(BadTextNodeClass):
        return False
    data = BadTextNodeClass.get(node)
    return reason in data.bad_reasons
