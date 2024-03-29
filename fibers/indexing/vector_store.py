from typing import List

import numpy as np


class VectorStore:
    def __init__(self):
        self.vectors = []
        self.weights = []
        self.items_to_index = {}
        self._vectors = None
        self.removed_items = set()
        self.similarity_function = similarity_by_exp

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

    def get_similarities(self, vec, items_to_search: List = None) -> [np.ndarray, List]:
        if self._vectors is None:
            self._vectors = np.array(self.vectors)
        if items_to_search is None:
            items_to_search = list(self.items_to_index.keys())
        item_indices = []
        remaining_items = []
        for item in items_to_search:
            if item in self.removed_items:
                continue
            vec_index_tuple = self.items_to_index.get(item, None)
            if vec_index_tuple is None:
                continue
            item_indices.extend(range(*vec_index_tuple))
            remaining_items.append(item)

        items_to_search = remaining_items

        # Decide the order of filtering by the number of items
        if len(items_to_search) > len(self.items_to_index) / 2:
            flatten_inner_prod = (self._vectors.dot(vec.T))[item_indices]
        else:
            flatten_inner_prod = self._vectors[item_indices].dot(vec)

        summed_similarities = self.similarity_function(self, flatten_inner_prod, item_indices, items_to_search)

        return summed_similarities, items_to_search


def similarity_by_exp(vector_store, flatten_inner_prod, item_indices, items_to_search):
    a = 2.0
    b = 0.1
    # Batch normalization & Add bias
    average_similarity = np.average(flatten_inner_prod)
    flatten_inner_prod = flatten_inner_prod - average_similarity - b
    # Add non-linearity
    flatten_inner_prod = np.exp(flatten_inner_prod * a)
    # Apply weights
    flatten_inner_prod = flatten_inner_prod.T * np.array(vector_store.weights)[item_indices]
    flatten_inner_prod = np.sum(flatten_inner_prod, axis=0)
    # Sum by node
    summed_similarities = np.zeros(len(items_to_search))
    for i in range(len(items_to_search)):
        vec_index_tuple = vector_store.items_to_index[items_to_search[i]]
        n_vecs = vec_index_tuple[1] - vec_index_tuple[0]
        summed_similarities[i] = np.sum(
            flatten_inner_prod[vec_index_tuple[0]:vec_index_tuple[1]]) / (n_vecs ** 0.5)
    return summed_similarities


