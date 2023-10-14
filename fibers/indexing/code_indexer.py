import json
from typing import List

from fibers.indexing.core import AbsEmbeddingIndexer, Indexing
from fibers.tree import Node


class CodeParameterIndexer(AbsEmbeddingIndexer):
    @classmethod
    def prepare_src_weight_list(cls, new_nodes: List[Node], indexing: Indexing,
                                ) -> (
            List[List[str]], List[List[float]], List[Node]):
        node_can_index = []
        contents = []
        weight_list = []
        for node in new_nodes:
            function = node.resource.get_resource_by_type("function")
            if function is not None and node.has_child("parameters") > 0:
                function_name = underscore_to_space(function.__name__)
                node_params = json.loads(node.s("parameters").content)
                for param_name, param_doc in node_params.items():
                    param_name = underscore_to_space(param_name)
                    if param_doc is not None:
                        contents.append([param_name, function_name, param_doc])
                        weight_list.append([0.4, 0.1, 0.5])
                    else:
                        contents.append([param_name, function_name])
                        weight_list.append([0.8, 0.2])
                    node_can_index.append(node)
        return contents, weight_list, node_can_index


class CodeReturnIndexer(AbsEmbeddingIndexer):
    @classmethod
    def prepare_src_weight_list(cls, new_nodes: List[Node], indexing: Indexing,
                                ) -> (
            List[List[str]], List[List[float]], List[Node]):
        node_can_index = []
        contents = []
        weight_list = []
        for node in new_nodes:
            function = node.resource.get_resource_by_type("function")
            if function is not None and node.has_child("return value"):
                if function.__annotations__["return"] is None:
                    continue
                contents_for_node = []
                weights_for_node = []
                function_name = underscore_to_space(function.__name__)
                node_can_index.append(node)
                contents_for_node.append(function_name)
                weights_for_node.append(1.0)
                if len(node.content) > 0:
                    contents_for_node.append(node.content)
                    weights_for_node.append(1.0)
                return_content = node.s("return value").content
                if len(return_content) > 0:
                    contents_for_node.append(return_content)
                    weights_for_node.append(2.0)
                contents.append(contents_for_node)
                weight_sum = sum(weights_for_node)
                weights_for_node = [w / weight_sum for w in weights_for_node]
                weight_list.append(weights_for_node)
        return contents, weight_list, node_can_index


class CodeDocsIndexer(AbsEmbeddingIndexer):
    @classmethod
    def prepare_src_weight_list(cls, new_nodes: List[Node], indexing: Indexing,
                                ) -> (
            List[List[str]], List[List[float]], List[Node]):
        node_can_index = []
        contents = []
        weight_list = []
        for node in new_nodes:
            function = node.resource.get_resource_by_type("function")
            if function is not None:
                function_name = underscore_to_space(function.__name__)
                node_can_index.append(node)
                contents.append([function_name])
                weight_list.append([1.0])
                print(function_name)
                if len(node.content) > 0:
                    node_can_index.append(node)
                    contents.append([node.content, function_name])
                    weight_list.append([0.7, 0.3])
                # for keyword in docs.keywords:
                #    node_can_index.append(node)
                #    contents.append([keyword, function_name])
                #    weight_list.append([0.6, 0.4])
        return contents, weight_list, node_can_index


def underscore_to_space(s: str):
    return s.replace("_", " ")
