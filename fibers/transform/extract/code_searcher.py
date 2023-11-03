from fibers.transform.decorate.code_summary import CodeSummarizedNodeClass
from fibers.transform.extract.traverser import beam_search
from fibers.tree import Node
from fibers.tree.node import NodeContentMap
from fibers.tree.node_class import CodeNodeClass


def code_beam_searcher(root: Node, requirement: str, code_type: str, content_map: NodeContentMap = None):
    assert code_type in ["function", "class", "section", "module"]
    assert requirement.startswith("The "+code_type)
    nodes_related = beam_search(root, requirement,
                                content_map)

    nodes_related = [node for node in nodes_related if
                     node.isinstance(CodeSummarizedNodeClass) and CodeNodeClass.get_type(
                         node) == code_type]

    return nodes_related