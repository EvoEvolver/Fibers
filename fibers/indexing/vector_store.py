import numpy as np


class VectorStore:
    def __init__(self):
        self.vectors = []
        self.items = []
        self.items_to_index = {}
        self._vectors = None
        self.removed_indices = []

    def add_vecs(self, vecs: List, items: List):
        assert len(vecs) == len(items)
        original_len = len(self.items)
        self.vectors.extend(vecs)
        self.items.extend(items)
        for i, item in enumerate(items):
            self.items_to_index[item] = original_len + i
        self._vectors = None

    def remove_items(self, items: List):
        removed_indices = []
        for item in items:
            index = self.items_to_index[item]
            removed_indices.append(index)
        # sort the indices
        removed_indices.sort()
        self.removed_indices = removed_indices
        if len(items) < len(self.items) / 3:
            return
        else:
            remaining_indices = self.get_remaining_indices()
            remaining_items = [self.items[i] for i in remaining_indices]
            self.items = remaining_items
            self.items_to_index = {self.items_to_index[item]: i for i, item in
                                   enumerate(remaining_items)}
            self._vectors = np.array(self.vectors)
            self._vectors = self._vectors[remaining_indices]
            self.vectors = self._vectors.tolist()
            self.removed_indices = []
            return

    def get_remaining_indices(self):
        remaining_indices = list(range(len(self.items)))
        for index in self.removed_indices:
            remaining_indices[index] = -1
        remaining_indices = [i for i in remaining_indices if i != -1]
        return remaining_indices

    def inner_product(self, vec, items: List = None):
        if self._vectors is None:
            self._vectors = np.array(self.vectors)
        if items is None:
            return self._vectors.dot(vec)
        indices = [self.items_to_index[item] for item in items]
        if len(items) > len(self.items) / 2:
            return (self._vectors.dot(vec))[indices]
        else:
            return self._vectors[indices].dot(vec)
