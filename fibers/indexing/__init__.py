from __future__ import annotations

from typing import List

import numpy as np

from fibers.tree import Node


class Indexing:
    def __init__(self, nodes: Node):
        pass

    def get_similarities(self, query: List[str], weights: List[float] = None,
                         items=None) -> (
            List[float], List[Node]):
        raise NotImplementedError

    def get_top_k_nodes(self, query: List[str], weights: List[float] = None, k: int = 10,
                        items=None) -> List[Node]:
        similarities, nodes = self.get_similarities(query, weights, items)
        node_rank = np.argsort(similarities)[::-1]
        node_added = set()
        top_k_nodes = []
        for i in range(len(node_rank)):
            node = nodes[node_rank[i]]
            if node not in node_added:
                top_k_nodes.append(node)
                node_added.add(node)
            if len(top_k_nodes) == k:
                break
        return top_k_nodes