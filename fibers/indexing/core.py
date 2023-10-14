from __future__ import annotations

import concurrent
import math
from typing import List, Type, Any, Callable, TYPE_CHECKING

import numpy as np

from fibers.helper.logger import Logger
from fibers.model.chat import Chat

if TYPE_CHECKING:
    from fibers.tree import Node
    from fibers.tree import Tree

from fibers.helper.cache_manage import save_cache, cached_function
from fibers.model.openai import get_embeddings


class Indexer:
    """
    An indexer is a class that takes in a list of nodes and returns a data structure that
    can be used to compute similarities between nodes.

    Indexer is stateless and its state is stored in the Indexing object.
    """

    @classmethod
    def make_data(cls, nodes: List[Node], indexing: Indexing):
        raise NotImplementedError

    @classmethod
    def get_similarities(cls, query: List[str], indexing: Indexing,
                         weights: List[float] = None):
        raise NotImplementedError

    @classmethod
    def remove_node(cls, node: Node):
        raise NotImplementedError


class Indexing:
    def __init__(self, nodes: List[Node], indexer: Type[Indexer],
                 tree: Tree):
        self.nodes_without_indexer: List[Node] = nodes[:]
        self.indexer: Type[Indexer] = indexer
        self.data: Any = None
        self.tree = tree

    def add_new_node(self, node: Node):
        self.nodes_without_indexer.append(node)

    def remove_node(self, node: Node):
        if node in self.nodes_without_indexer:
            self.nodes_without_indexer.remove(node)

    def make_data(self):
        self.indexer.make_data(self.nodes_without_indexer, self)

    def get_similarities(self, query: List[str], weights: List[float] = None) -> (
            List[float], List[Node]):
        if len(self.nodes_without_indexer) > 0:
            self.make_data()
        return self.indexer.get_similarities(query, self, weights)

    def get_top_k_nodes(self, query: List[str], weights: List[float] = None, k: int = 10,
                        node_filter: Callable[[Node], bool] = None) -> List[Node]:
        similarities, nodes = self.get_similarities(query, weights)
        node_rank = np.argsort(similarities)[::-1]
        node_added = set()
        top_k_nodes = []
        node_filter = node_filter if node_filter is not None else lambda node: True
        for i in range(len(node_rank)):
            node = nodes[node_rank[i]]
            if node not in node_added and node_filter(node):
                top_k_nodes.append(node)
                node_added.add(node)
            if len(top_k_nodes) == k:
                break
        return top_k_nodes


class Query:
    def __init__(self, query, query_type: str = "similarity"):
        """
        :param query: The content of the query
        :param query_type: The type of the query. It can be "similarity" or "question" or any other type the indexer supports
            if the indexer does not support the query type, it will treat it as a similarity query
        """
        self.query = query
        self.query_type = query_type


class IndexingSearchLogger(Logger):
    active_loggers = []

    def display_log(self):
        from fibers.gui.similarity_search import draw_similarity_gui
        for log in self.log_list:
            draw_similarity_gui(*log)


class AbsEmbeddingIndexer(Indexer):
    @classmethod
    def prepare_src_weight_list(cls, new_nodes: List[Node], indexing: Indexing,
                                ) -> (
            List[List[str]], List[List[float]], List[Node]):
        """
        Select nodes that will be indexed and return a list of srcs and weights for each
        :param new_nodes: The incoming nodes
        :param indexing: The indexing object
        :return: A triplet of srcs, weights, and nodes
        """
        raise NotImplementedError

    @classmethod
    def make_data(cls, new_nodes: List[Node], indexing: Indexing):
        if indexing.data is None:
            indexing.data = {
                "vecs": None,
                "srcs_list": [],
                "node_of_vecs": [],
                "weights_list": [],
            }

        new_srcs, new_weights, new_node_of_vecs = cls.prepare_src_weight_list(new_nodes,
                                                                              indexing)
        indexing.data["srcs_list"].extend(new_srcs)
        indexing.data["node_of_vecs"].extend(new_node_of_vecs)
        indexing.data["weights_list"].extend(new_weights)

        new_vecs = []
        flattened_src_list = []
        flattened_weight_list = []

        children_index_start = []
        for i, srcs in enumerate(new_srcs):
            if len(srcs) == 0:
                children_index_start.append(-1)
                continue
            children_index_start.append(len(flattened_src_list))
            flattened_src_list.extend(srcs)
            flattened_weight_list.extend(new_weights[i])

        src_embedding_list = np.array(get_embeddings(flattened_src_list, make_cache=True))

        weighted_embeddings = (src_embedding_list.T * np.array(
            flattened_weight_list)).T

        embedding_dim = len(src_embedding_list[0])

        for i, start_index in enumerate(children_index_start):
            if start_index == -1:
                new_vecs.append(np.zeros(embedding_dim))
                continue
            child_embedding_list = weighted_embeddings[start_index: start_index + len(
                new_srcs[i])]
            new_vecs.append(
                np.sum(child_embedding_list, axis=0))

        # Merge new_vecs with existing vecs

        new_vecs = np.array(new_vecs)
        if indexing.data["vecs"] is None:
            indexing.data["vecs"] = np.array(new_vecs)
        else:
            existing_vecs = indexing.data["vecs"]
            concatenated_vecs = np.concatenate([existing_vecs, new_vecs])
            indexing.data["vecs"] = concatenated_vecs

    @classmethod
    def get_similarities(cls, query: List[str], indexing: Indexing,
                         weights: List[float] = None) -> (List[float], List[Node]):

        text_embedding_list = get_embeddings(query, make_cache=True)
        vecs = indexing.data["vecs"]
        if len(vecs) == 0:
            return [], []

        text_embedding_list = np.array(text_embedding_list)
        similarity = vecs.dot(text_embedding_list.T).T

        if weights is None:
            weights = [1.0] * len(vecs)

        average_similarity = np.average(similarity, axis=1)
        similarity = similarity.T - average_similarity - 0.05
        # add non-linearity to similarity
        similarity = np.exp(similarity * 2)
        similarity = similarity * weights

        similarity = np.sum(similarity, axis=1)

        if len(IndexingSearchLogger.active_loggers) > 0:
            IndexingSearchLogger.add_log_to_all(
                show_src_similarity_gui(similarity, indexing.data, query, weights))

        return similarity, indexing.data["node_of_vecs"]

    @classmethod
    def process_node_with_content(cls, nodes: List[Node], indexing: Indexing,
                                  ):
        raise NotImplementedError

    @classmethod
    def process_node_without_content(cls, nodes: List[Node], indexing: Indexing,
                                     ):
        raise NotImplementedError


def show_src_similarity_gui(similarity, data, query, weights, top_k=10):
    top_node_index = np.argsort(similarity)[::-1][:top_k]
    nodes = data["node_of_vecs"]
    top_nodes = [nodes[i] for i in top_node_index]
    contents = [node.content for node in top_nodes]
    src_list = data["srcs_list"]
    src_list = [src_list[i] for i in top_node_index]
    return src_list, weights, query, contents


class FragmentedEmbeddingIndexer(AbsEmbeddingIndexer):
    @classmethod
    def process_node_with_content(cls, nodes: List[Node], indexing: Indexing,
                                  ):
        nodes_content = [node.content for node in nodes]
        tree = indexing.tree

        new_src_list = []
        new_weights = []
        n_finished = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for node, frags in zip(nodes,
                                   executor.map(process_sent_into_frags, nodes_content)):
                new_src = []
                new_src.extend(frags)
                node_path = tree.get_node_path(node)
                if len(node_path) > 0:
                    new_src.append(tree.get_node_path(node)[-1])
                new_src.append(node.content)

                new_src_list.append(new_src)
                # TODO Handle when there are too many fragments. Maybe we should group
                #  them by clustering
                weight = np.ones(len(new_src)) / (len(new_src) ** 0.95)
                new_weights.append(weight)

                n_finished += 1
                if n_finished % 20 == 19:
                    save_cache()

        save_cache()
        return new_src_list, new_weights

    @classmethod
    def process_node_without_content(cls, nodes: List[Node], indexing: Indexing,
                                     ):
        new_src_list = []
        new_weights = []

        for node in nodes:
            keywords_on_path = node.node_path()
            # keep last 1/3 of the keywords
            n_keywords = min(max(math.ceil(len(keywords_on_path) / 3), 3),
                             len(keywords_on_path))
            new_src = keywords_on_path[-n_keywords:]
            new_src_list.append(new_src)
            weight = np.array([i + 1 for i in range(len(new_src))])
            weight = weight / np.sum(weight)
            new_weights.append(weight)

        return new_src_list, new_weights

    @classmethod
    def prepare_src_weight_list(cls, new_nodes: List[Node], indexing: Indexing,
                                ):

        tree = indexing.tree
        nodes_with_content = []
        nodes_content = []
        nodes_without_content = []
        for node in new_nodes:
            if len(node.content) == 0:
                keywords_on_path = tree.get_node_path(node)
                if len(keywords_on_path) != 0:
                    nodes_without_content.append(node)
                continue
            nodes_with_content.append(node)
            nodes_content.append(node.content)

        new_src_list_1, new_weights_1 = cls.process_node_without_content(
            nodes_without_content, indexing)

        new_src_list_2, new_weights_2 = cls.process_node_with_content(
            nodes_with_content, indexing)

        new_src_list = new_src_list_1 + new_src_list_2
        new_weights = new_weights_1 + new_weights_2
        new_nodes = nodes_without_content + nodes_with_content

        assert len(new_src_list) == len(new_weights) == len(new_nodes)

        return new_src_list, new_weights, new_nodes


prompt_for_splitting = "Split the following sentence into smaller fragments (no more than about 8 words). Put each fragment in a new line."
prompt_for_extracting = "Give some phrases that summarize the following sentence. The phrases should be no more than 8 words and represents what the sentence is describing. Put each phrase in a new line."

@cached_function("sent_breaking")
def process_sent_into_frags(sent: str,
                            prompt=prompt_for_extracting):

    system_message = ("You are a helpful processor for NLP problems. Answer anything "
                      "concisely and parsable. Use newline to separate multiple answers.")

    chat = Chat(
        user_message=prompt,
        system_message=system_message)
    chat.add_user_message("Sentence: "+sent)
    res = chat.complete_chat()
    res = res.split('\n')

    # filter out empty lines
    res = [line for line in res if len(line.strip()) != 0]

    if res[0][0] == "-":
        for i in range(len(res)):
            if res[i][0] == "-":
                res[i] = res[i][1:].strip()

    for i in range(len(res)):
        if "," in res[i]:
            keys = res[i].split(",")
            res[i] = keys[0]
            res.extend(keys[1:])

    res = [line for line in res if len(line.strip()) != 0]

    return res
