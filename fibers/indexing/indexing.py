from __future__ import annotations

from typing import List, Callable, Tuple

import numpy as np

from fibers.indexing.vector_store import VectorStore
from mllm import get_embeddings

from fibers.tree import Node


class Indexing:
    def __init__(self, nodes: List[Node]):
        self.add_nodes(nodes)

    def add_nodes(self, nodes: List[Node]):
        raise NotImplementedError

    def remove_nodes(self, nodes: List[Node]):
        raise NotImplementedError

    def get_similarities(self, query, nodes=None) -> (List[float], List[Node]):
        raise NotImplementedError

    def get_top_k_nodes(self, query, k: int = 10,
                        items=None) -> List[Node]:
        raise NotImplementedError


WeightedContent = Tuple[str, float]
WeightedContentGetter = Callable[[Node], List[WeightedContent]]
default_weighted_content_getter: WeightedContentGetter = lambda node: [(node.content, 1.0)]

class VectorIndexing(Indexing):
    def __init__(self, nodes: List[Node],
                 get_weighted_contents: WeightedContentGetter = None):
        self.vector_store = VectorStore()
        self.get_weighted_contents: WeightedContentGetter = get_weighted_contents or default_weighted_content_getter
        super().__init__(nodes)


    def add_nodes(self, nodes: List[Node]):
        vecs, nodes = self.get_vectors(nodes)
        self.vector_store.add_vecs(vecs, nodes)

    def remove_nodes(self, nodes: List[Node]):
        self.vector_store.remove_items(nodes)

    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        non_empty_nodes = []
        contents = []
        for node in nodes:
            content_weight_tuples = self.get_weighted_contents(node)
            for content, weight in content_weight_tuples:
                if len(content) > 0 and weight > 0.0:
                    non_empty_nodes.append(node)
                    contents.append(content)
        text_embeddings = get_embeddings(contents)
        return text_embeddings, non_empty_nodes

    def get_similarities(self, query: str | List[str], nodes=None) -> (List[float], List[Node]):
        if isinstance(query, str):
            query_tensor = self.get_query_vector(query)
        else:
            query_tensor = np.array(
                [self.get_query_vector(query) for query in query])
        similarities, nodes = self.vector_store.get_similarities(query_tensor, nodes)
        return similarities, nodes

    def get_top_k_nodes(self,
                        query: str | List[str],
                        k: int = 10,
                        items=None) -> List[Node]:
        similarities, nodes = self.get_similarities(query, items)
        top_k = top_k_node_by_similarity(similarities, nodes, k)
        return top_k

    def get_query_vector(self, query) -> np.ndarray:
        text_embedding = get_embeddings([query])
        return np.array(text_embedding[0])


class ComplexIndexing(Indexing):
    def __init__(self, nodes):
        self.indexings = []
        super().__init__(nodes)

    def add_nodes(self, nodes: List[Node]):
        for indexing in self.indexings:
            indexing.add_nodes(nodes)

    def remove_nodes(self, nodes: List[Node]):
        for indexing in self.indexings:
            indexing.remove_nodes(nodes)

    def get_similarities(self, query, nodes=None) -> (List[float], List[Node]):
        raise NotImplementedError

    def get_top_k_nodes(self, query, k: int = 10,
                        items=None) -> List[Node]:
        similarities, nodes = self.get_similarities(query, items)
        top_k = top_k_node_by_similarity(similarities, nodes, k)
        return top_k


def top_k_node_by_similarity(similarities, nodes, k):
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
