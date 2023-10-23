from typing import List, Dict

import numpy as np

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.indexing.indexing import ComplexIndexing, VectorIndexing
from fibers.model.embedding import get_embeddings
from fibers.tree import Tree, Node


class CodeIndexing(ComplexIndexing):
    def __init__(self, tree: Tree):
        super().__init__(tree.all_nodes())
        self.indexings = [
            DescriptionIndexing(tree),
            ParameterIndexing(tree)
        ]

    def get_similarities(self, query, nodes=None) -> (List[float], List[Node]):
        desc_indexing = self.indexings[0]
        param_indexing = self.indexings[1]
        if len(query) == 1:
            if query.get("desc") is not None:
                return desc_indexing.get_similarities(query["desc"], nodes)
            elif query.get("param") is not None:
                return param_indexing.get_similarities(query["param"], nodes)
            else:
                raise
        desc_similarities, desc_nodes = desc_indexing.get_similarities(query["desc"],
                                                                       nodes)
        param_similarities, param_nodes = param_indexing.get_similarities(query["param"],
                                                                          nodes)
        desc_similarities = np.array(desc_similarities)
        param_similarities = np.array(param_similarities)
        # Normalize the similarities
        desc_similarities = desc_similarities / np.max(desc_similarities)
        param_similarities = param_similarities / np.max(param_similarities)
        similarity_dict = {}
        for i, similarity in enumerate(desc_similarities):
            node = desc_nodes[i]
            similarity_dict[node] = similarity
        for i, similarity in enumerate(param_similarities):
            node = desc_nodes[i]
            similarity_dict[node] += 0.8 * similarity
        similarities = list(similarity_dict.values())
        nodes = list(similarity_dict.keys())
        return similarities, nodes


class EnvironmentIndexing(VectorIndexing):
    def __init__(self, tree: Tree):
        super().__init__(tree.all_nodes())


class DescriptionIndexing(VectorIndexing):
    def __init__(self, tree: Tree):
        super().__init__(tree.all_nodes())

    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        non_empty_nodes = []
        contents = []
        for node in nodes:
            if node.resource.has_type("function") and not node.is_empty:
                non_empty_nodes.append(node)
                contents.append(node.path()[-1] + "\n" + node.content)
        text_embeddings = get_embeddings(contents)
        return text_embeddings, non_empty_nodes


class ParameterIndexing(VectorIndexing):
    def __init__(self, tree: Tree):
        super().__init__(tree.all_nodes())

    @staticmethod
    def param_dict_to_str(param_dict: Dict[str, str]):
        param_embed_src = ["Parameters:"]
        for param_name, param_doc in param_dict.items():
            if len(param_doc) > 0:
                param_embed_src.append(param_name + ": " + param_doc)
            else:
                param_embed_src.append(param_name)
        return "\n".join(param_embed_src)

    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        non_empty_nodes = []
        contents = []
        for node in nodes:
            if node.resource.has_type("function"):
                parameters = node.resource.get_resource_by_key("parameters")
                if parameters is None:
                    continue
                contents.append(self.param_dict_to_str(parameters))
                non_empty_nodes.append(node)
        text_embeddings = get_embeddings(contents)
        return text_embeddings, non_empty_nodes

    def get_query_vector(self, query: Dict) -> np.ndarray:
        text_embedding = get_embeddings([self.param_dict_to_str(query)])
        return np.array(text_embedding[0])


if __name__ == "__main__":
    from fibers.testing.testing_modules import v_lab
    tree = get_tree_for_module(v_lab)
    indexing = CodeIndexing(tree)
    nodes = indexing.get_top_k_nodes({"desc": "get a beaker of water"}, 2)
