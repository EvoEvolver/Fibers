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
    node.add_class(BadTextNodeClass)
    data = BadTextNodeClass.get_data(node)
    if "bad_reasons" not in data:
        data["bad_reasons"] = set()
    data["bad_reasons"].add(reason)


def remove_bad_reason(node, reason: str):
    data = BadTextNodeClass.get_data(node)
    if "bad_reasons" not in data:
        return
    if reason in data["bad_reasons"]:
        data["bad_reasons"].remove(reason)
    if len(data["bad_reasons"]) == 0:
        node.remove_class(BadTextNodeClass)


def has_bad_reason(node, reason: str) -> bool:
    if not node.isinstance(BadTextNodeClass):
        return False
    data = BadTextNodeClass.get_data(node)
    if "bad_reasons" not in data:
        return False
    return reason in data["bad_reasons"]
