from typing import List

from fibers import debug
from fibers.compose.decorate.text_summary import TextSummary
from fibers.helper.cache.cache_service import caching
from fibers.helper.utils import RobustParse, standard_multi_attempts
from fibers.indexing.code.core import get_code_indexing
from fibers.indexing.indexing import VectorIndexing
from fibers.model.chat import Chat
from fibers.compose.decorate.code_summary import CodeSummary
from fibers.compose.extract.beam_search import beam_search
from fibers.tree import Node, Tree
from fibers.tree.node import ContentMap
from fibers.tree.node_class.code_node import get_type
from fibers.tree.prompt_utils import get_node_list_prompt


class CodeSearcher:
    def __init__(self, root: Node):
        self.content_map = ContentMap(
            lambda n: CodeSummary.get_summary(n) or n.content)
        self.root = root
        self.vector_indexing = get_code_indexing(root)#VectorIndexing(list(root.iter_subtree_with_dfs()), self.content_map)

    def search(self, requirement: str, code_types: List[str]):
        for code_type in code_types:
            assert code_type in ["function", "class", "section", "module", "example"]
        with debug.refresh_cache():
            nodes_from_beam = beam_search(self.root, requirement, self.content_map)
        descriptions = get_code_descriptions(requirement)
        nodes_from_vector = []
        for description in descriptions:
            nodes_from_vector += self.vector_indexing.get_top_k_nodes(description, 5)
        nodes_related = list(set(nodes_from_beam + nodes_from_vector))
        nodes_related = [node for node in nodes_related if get_type(
                         node) in code_types]
        if len(nodes_related) == 0:
            return []

        nodes_related = filter_code_nodes(nodes_related,
                                          requirement + "\nYou must select at least one index unless it is totally not related.",
                                          self.content_map)
        return nodes_related


@standard_multi_attempts
def get_code_descriptions(requirement: str):
    prompt = f"""
You are trying to find Python functions based on a requirement:
{requirement}
<requirement end>

Your task is to reduce the requirement into more specific sentences, which covers
- The (possible) names of the function
- The arguments of the function
- The return values of the function
- What the function does

Notice that the requirement may need multiple functions to satisfy.

You should output a JSON dict whose key is like "function 1", "function 2", ... and the value is a list of sentences that describe the function. The sentences should resemble the description of the function that their author would write in the documentation of the function. All the sentences should start with "The function". Your sentences should be concise. The sentences should not includes too much information that is not from the requirement.
"""
    chat = Chat(system_message="You are a smart assistant who only output in JSON.")
    chat.add_user_message(prompt)
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    return list(res.values())




class DocsSearcher:
    def __init__(self, root: Node):
        self.content_map = ContentMap(
            lambda n: TextSummary.get(n).text_summary or n.content)
        self.root = root
        self.vector_indexing = VectorIndexing(list(root.iter_subtree_with_dfs()), self.content_map)

    def search(self, requirement: str):
        nodes_from_beam = beam_search(self.root, requirement,
                                    self.content_map)
        nodes_from_vector = self.vector_indexing.get_top_k_nodes(requirement, 5)
        nodes_related = list(set(nodes_from_beam + nodes_from_vector))

        if len(nodes_related) == 0:
            return []

        nodes_related = [node for node in nodes_related if not node.is_empty()]

        nodes_related = filter_docs_nodes(nodes_related,
                                          requirement,
                                          self.content_map)
        return nodes_related


def filter_docs_nodes(nodes: List[Node], requirement: str, content_map):
    prompt = f"""
Here are a few documents:
{get_node_list_prompt(nodes, content_map)}

You are trying to find the documents that most satisfy the following requirement:
{requirement}

Output the indices that matches the requirement the most by a JSON dict with key "indices" whose value is a list of numbers. If you are not sure, output an empty list.
"""
    chat = Chat(user_message=prompt,
                system_message="You are a helpful assistant who output in JSON.")
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    res = res["indices"]
    matched_node = [nodes[i] for i in res]
    return matched_node


@standard_multi_attempts
def filter_code_nodes(nodes: List[Node], requirement: str, content_map):
    prompt = f"""
Here are a few Python objects:
{get_node_list_prompt(nodes, content_map)}

You are trying to find Python objects that most satisfy the following requirement:
{requirement}

Output the indices that meet the requirement the most by a JSON dict with key "indices" whose value is a list of numbers.
"""
    chat = Chat(user_message=prompt,
                system_message="You are a very smart assistant.")
    res = chat.complete_chat_expensive()
    print(chat)
    res = RobustParse.dict(res)
    res = res["indices"]
    matched_node = [nodes[i] for i in res]
    return matched_node


if __name__ == '__main__':
    req = "The function helps achieve the following: Call the vision model function with the new frequency and new phase gradient data to analyze for a significant peak."
    import q_lab
    from fibers.compose.agent import tool_box
    from fibers.data_loader.module_to_tree import add_module_tree_to_node
    tree = Tree("Moduler")
    add_module_tree_to_node(q_lab, tree.root)
    add_module_tree_to_node(tool_box, tree.root)
    tree.show_tree_gui_react()
    searcher = CodeSearcher(tree.root)
    print(searcher.search(req, ["function"]))