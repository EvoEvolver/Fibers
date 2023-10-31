from fibers.tree.node_class import NodeClass


class BadTextNodeClass(NodeClass):
    @staticmethod
    def add_bad_reason(node, reason: str):
        add_bad_reason(node, reason)

    @staticmethod
    def remove_bad_reason(node, reason: str):
        remove_bad_reason(node, reason)

    @staticmethod
    def has_bad_reason(node, reason: str) -> bool:
        return has_bad_reason(node, reason)

def add_bad_reason(node, reason: str):
    assert reason in ["overlap_to_sibling", "bad_title"]
    if "bad_reasons" not in node.meta:
        node.meta["bad_reasons"] = set()
    node.meta["bad_reasons"].add(reason)
    node.add_class(BadTextNodeClass)

def remove_bad_reason(node, reason: str):
    if "bad_reasons" not in node.meta:
        return
    node.meta["bad_reasons"].remove(reason)
    if len(node.meta["bad_reasons"]) == 0:
        node.remove_class(BadTextNodeClass)

def has_bad_reason(node, reason: str)->bool:
    if "bad_reasons" not in node.meta:
        return False
    return reason in node.meta["bad_reasons"]