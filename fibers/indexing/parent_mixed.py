from typing import List

import numpy as np

from fibers.helper.utils import add_to_flat_list, make_nested_list
from mllm import get_embeddings

from fibers.indexing.indexing import VectorIndexing
from fibers.tree import Node
from fibers.tree.node import ContentMap


class ParentMixedIndexing(VectorIndexing):

    def __init__(self, nodes, content_map: ContentMap):
        self.content_map = content_map
        super().__init__(nodes)

    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        non_empty_nodes = []
        contents = []
        weights = []
        for node in nodes:
            if len(node.content) > 0:
                non_empty_nodes.append(node)
                content, weight = ParentMixedIndexing.get_source_content(self.content_map, node)
                contents.append(content)
                weights.append(weight)
        flattened_contents = []
        flattened_weights = []
        add_to_flat_list(flattened_contents, contents)
        add_to_flat_list(flattened_weights, weights)
        flattened_embeddings = get_embeddings(flattened_contents)
        flattened_embeddings = np.array(flattened_weights)[:, None] * flattened_embeddings
        embeddings = make_nested_list(list(flattened_embeddings), contents)
        summed_embeddings = [np.sum(embedding, axis=0) for embedding in embeddings]
        return summed_embeddings, non_empty_nodes

    def get_query_vector(self, query) -> np.ndarray:
        function_name, function_summary = query
        text_embedding = get_embeddings([function_name+": "+function_summary])
        return np.array(text_embedding[0])

    @staticmethod
    def get_source_content(content_map: ContentMap, node: Node) -> (List[str], List[float]):
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
            source_contents.append(title+": "+content)
        source_weight = [1.0, 0.2, 0.1][:len(source_contents)]
        weight_sum = sum(source_weight)
        source_weight = [w / weight_sum for w in source_weight]
        return source_contents, source_weight
