from typing import List

import numpy as np


class VectorStore:
    def __init__(self):
        self.vectors = []
        self.items_to_index = {}
        self._vectors = None
        self.removed_items = set()

    def add_vecs(self, vecs: List, items: List):
        assert len(vecs) == len(items)
        original_len = len(self.items_to_index)
        self.vectors.extend(vecs)
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
        for item in self.items_to_index.keys():
            vectors_for_item = self.vectors[
                               self.items_to_index[item][0]:self.items_to_index[item][1]]
            new_items_to_index[item] = [len(new_vectors),
                                        len(new_vectors) + len(vectors_for_item)]
            new_vectors.extend(vectors_for_item)
        self.vectors = new_vectors
        self.items_to_index = new_items_to_index
        self._vectors = None

    def inner_product(self, vec, items: List = None) -> [np.ndarray, List]:
        if self._vectors is None:
            self._vectors = np.array(self.vectors)
        if items is None:
            items = self.items_to_index.keys()
        indices = []
        nodes = []
        for item in items:
            if item in self.removed_items:
                continue
            vec_index_tuple = self.items_to_index[item]
            indices.extend(range(*vec_index_tuple))
            nodes.extend([item] * (vec_index_tuple[1] - vec_index_tuple[0]))
        if len(items) > len(self.items_to_index) / 2:
            return (self._vectors.dot(vec))[indices], nodes
        else:
            return self._vectors[indices].dot(vec), nodes
