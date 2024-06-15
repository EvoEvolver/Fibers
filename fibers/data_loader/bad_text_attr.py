from fibers.tree.node_attr import Attr


class BadText(Attr):
    def __init__(self, node):
        super().__init__(node)
        self.bad_reasons = set()

    def add_bad_reason(self, reason: str):
        assert reason in ["overlap_to_sibling", "bad_title"]
        self.bad_reasons.add(reason)

    def remove_bad_reason(self, reason: str):
        if reason in self.bad_reasons:
            self.bad_reasons.remove(reason)

    def has_bad_reason(self, reason: str) -> bool:
        return reason in self.bad_reasons
