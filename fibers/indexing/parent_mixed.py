from typing import List

import numpy as np
from fibers.model.embedding import get_embeddings

from fibers.indexing.indexing import VectorIndexing
from fibers.tree import Node
from fibers.tree.node import NodeContentMap


class KeyPhraseIndexing(VectorIndexing):

    def __init__(self, nodes, content_map: NodeContentMap):
        super().__init__(nodes)
        self.content_map = content_map

    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        non_empty_nodes = []
        contents = []
        for node in nodes:
            if len(node.content) > 0:
                non_empty_nodes.append(node)
                contents.append(node.content)
        text_embeddings = get_embeddings(contents)
        return text_embeddings, non_empty_nodes

    @staticmethod
    def get_source_content(content_map: NodeContentMap, node: Node) -> (List[str], List[float]):
        source_nodes = [node]
        parent = node.parent()
        if parent is not None:
            source_nodes.append(parent)
            grand_parent = parent.parent()
            if grand_parent is not None:
                source_nodes.append(grand_parent)
        source_contents = []
        for node in source_nodes:
            title, content = content_map.get_title_and_content(node)
            source_contents.append("title"+":"+content)
        source_weight = [1.0, 0.5, 0.25][:len(source_contents)]
        weight_sum = sum(source_weight)
        source_weight = [w / weight_sum for w in source_weight]
        return source_contents, source_weight
