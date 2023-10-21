import concurrent
import math
from typing import List

import numpy as np

from fibers.helper.cache.cache_service import cache_service, cached_function
from fibers.indexing.indexing import VectorIndexing
from fibers.model.chat import Chat
from fibers.model.embedding import get_embeddings
from fibers.tree import Node


class KeyPhraseIndexing(VectorIndexing):
    def get_vectors(self, nodes: List[Node]) -> [List[np.ndarray], List[Node]]:
        src_list, weights, nodes = self.prepare_src_weight_list(nodes)
        for i in range(len(src_list)):
            nodes[i].meta["__indexing_key_phrase"] = src_list[i]
        flattened_src_list = []
        flattened_weights = []
        flattened_nodes = []
        i = 0
        for src, weight in zip(src_list, weights):
            flattened_src_list.extend(src)
            flattened_weights.extend(weight)
            flattened_nodes.extend([nodes[i]] * len(src))
            i += 1
        flattened_weights = np.array(flattened_weights)
        text_embeddings = get_embeddings(flattened_src_list)
        #text_embeddings = np.array(text_embeddings) * flattened_weights[:, None]
        return text_embeddings, flattened_nodes

    @staticmethod
    def process_node_with_content(nodes: List[Node]):
        nodes_content = [node.content for node in nodes]

        new_src_list = []
        new_weights = []
        n_finished = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for node, frags in zip(nodes,
                                   executor.map(break_into_key_phrases, nodes_content)):
                new_src = []
                new_src.extend(frags)
                node_path = node.node_path()
                if len(node_path) > 0:
                    new_src.append(node.node_path()[-1])
                new_src.append(node.content)

                new_src_list.append(new_src)
                # TODO Handle when there are too many fragments. Maybe we should group
                #  them by clustering
                weight = np.ones(len(new_src)) / (len(new_src) ** 0.95)
                new_weights.append(weight)

                n_finished += 1
                if n_finished % 20 == 19:
                    cache_service.save_cache()

        cache_service.save_cache()
        return new_src_list, new_weights

    @staticmethod
    def process_node_without_content(nodes: List[Node]):
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

    @staticmethod
    def prepare_src_weight_list(new_nodes: List[Node]):
        nodes_with_content = []
        nodes_content = []
        nodes_without_content = []
        for node in new_nodes:
            if len(node.content) == 0:
                keywords_on_path = node.node_path()
                if len(keywords_on_path) != 0:
                    nodes_without_content.append(node)
                continue
            nodes_with_content.append(node)
            nodes_content.append(node.content)

        new_src_list_1, new_weights_1 = KeyPhraseIndexing.process_node_without_content(
            nodes_without_content)
        new_src_list_2, new_weights_2 = KeyPhraseIndexing.process_node_with_content(
            nodes_with_content)

        new_src_list = new_src_list_1 + new_src_list_2
        new_weights = new_weights_1 + new_weights_2
        new_nodes = nodes_without_content + nodes_with_content

        assert len(new_src_list) == len(new_weights) == len(new_nodes)

        return new_src_list, new_weights, new_nodes


prompt_for_splitting = "Split the following sentence into smaller fragments (no more than about 8 words). Put each fragment in a new line."
prompt_for_extracting = "Give some phrases that summarize the following sentence. The phrases should be no more than 8 words and represents what the sentence is describing. Put each phrase in a new line."


@cached_function("key_phrases")
def break_into_key_phrases(sent: str,
                           prompt=prompt_for_extracting):
    system_message = ("You are a helpful processor for NLP problems. Answer anything "
                      "concisely and parsable. Use newline to separate multiple answers.")

    chat = Chat(
        user_message=prompt,
        system_message=system_message)
    chat.add_user_message("Sentence: " + sent)
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
