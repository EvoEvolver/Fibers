from __future__ import annotations

from typing import List

import numpy as np

from fibers.indexing.vector_store import VectorStore
from fibers.model.embedding import get_embeddings

from fibers.tree import Node
from fibers.tree.node import ContentMap


class Indexing:
    def __init__(self, nodes: List[Node], content_map: ContentMap = None):
        self.content_map = content_map or ContentMap()
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


class VectorIndexing(Indexing):
    def __init__(self, nodes: List[Node], content_map: ContentMap = None):
        self.vector_store = VectorStore()
        super().__init__(nodes, content_map)

    def add_nodes(self, nodes: List[Node]):
        vecs, nodes = self.get_vectors(nodes)
        self.vector_store.add_vecs(vecs, nodes)

    def remove_nodes(self, nodes: List[Node]):
        self.vector_store.remove_items(nodes)

    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        non_empty_nodes = []
        contents = []
        for node in nodes:
            title, content = self.content_map.get_title_and_content(node)
            if len(content) > 0:
                non_empty_nodes.append(node)
                contents.append(content)
        text_embeddings = get_embeddings(contents)
        return text_embeddings, non_empty_nodes

    def get_similarities(self, query, nodes=None) -> (List[float], List[Node]):
        query_vector = self.get_query_vector(query)
        similarities, nodes = self.vector_store.get_similarities(query_vector, nodes)
        return similarities, nodes

    def get_top_k_nodes(self, query, k: int = 10,
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
