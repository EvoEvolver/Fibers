from typing import List

import numpy as np


class VectorStore:
    def __init__(self):
        self.vectors = []
        self.weights = []
        self.items_to_index = {}
        self._vectors = None
        self.removed_items = set()

    def add_vecs(self, vecs: List, items: List, weights: List = None):
        assert len(vecs) == len(items)
        original_len = len(self.items_to_index)
        self.vectors.extend(vecs)
        if weights is None:
            weights = np.ones(len(vecs))
        self.weights.extend(weights)
        for i, item in enumerate(items):
            index_start = i + original_len
            if item not in self.items_to_index:
                self.items_to_index[item] = [index_start, index_start + 1]
            else:
                self.items_to_index[item][1] = index_start + 1
        self._vectors = None

    def remove_items(self, items: List):
        self.removed_items.update(items)
        if len(items) > len(self.items_to_index) / 3:
            self.flush_removed_indices()

    def flush_removed_indices(self):
        removed_indices = []
        for item in self.removed_items:
            if item in self.items_to_index:
                removed_indices.extend(range(*self.items_to_index[item]))
                del self.items_to_index[item]
        new_vectors = []
        new_items_to_index = {}
        new_weights = []
        for item in self.items_to_index.keys():
            indices_tuple = self.items_to_index[item]
            vectors_for_item = self.vectors[indices_tuple[0]:indices_tuple[1]]
            new_items_to_index[item] = [len(new_vectors),
                                        len(new_vectors) + len(vectors_for_item)]
            new_vectors.extend(vectors_for_item)
            new_weights.extend(self.weights[indices_tuple[0]:indices_tuple[1]])
        self.weights = new_weights
        self.vectors = new_vectors
        self.items_to_index = new_items_to_index
        self._vectors = None

    def get_similarities(self, vec, items: List = None) -> [np.ndarray, List]:
        if self._vectors is None:
            self._vectors = np.array(self.vectors)
        if items is None:
            items = list(self.items_to_index.keys())
        indices = []
        nodes = []
        for item in items:
            if item in self.removed_items:
                continue
            vec_index_tuple = self.items_to_index[item]
            indices.extend(range(*vec_index_tuple))
            nodes.append(item)

        if len(items) > len(self.items_to_index) / 2:
            flatten_similarities = (self._vectors.dot(vec))[indices]
        else:
            flatten_similarities = self._vectors[indices].dot(vec)

        average_similarity = np.average(flatten_similarities)
        flatten_similarities = flatten_similarities - average_similarity - 0.05
        flatten_similarities = np.exp(flatten_similarities * 2)
        flatten_similarities = flatten_similarities * np.array(self.weights)[indices]
        summed_similarities = np.zeros(len(nodes))
        for i in range(len(nodes)):
            vec_index_tuple = self.items_to_index[nodes[i]]
            summed_similarities[i] = np.sum(
                flatten_similarities[vec_index_tuple[0]:vec_index_tuple[1]])

        return summed_similarities, nodes
