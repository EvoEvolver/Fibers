from typing import List

from fibers.model.chat import Chat
from fibers.compose.decorate.code_summary import CodeSummarizedNodeClass
from fibers.compose.extract.traverser import beam_search
from fibers.tree import Node
from fibers.tree.node import ContentMap
from fibers.tree.node_class.code_node import get_type
from fibers.tree.prompt_utils import get_node_list_prompt


def code_beam_searcher(root: Node, requirement: str, code_type: str, content_map: ContentMap = None):
    assert code_type in ["function", "class", "section", "module"]
    assert requirement.startswith("The "+code_type)
    nodes_related = beam_search(root, requirement,
                                content_map)

    nodes_related = [node for node in nodes_related if
                     node.isinstance(CodeSummarizedNodeClass) and get_type(
                         node) == code_type]
    if len(nodes_related) == 0:
        return None
    nodes_related = filter_code_nodes(nodes_related, requirement+"\nYou must select exactly one index", content_map)
    return nodes_related

def filter_code_nodes(nodes: List[Node], requirement: str, content_map):
    prompt = f"""
Here are a few Python objects:
{get_node_list_prompt(nodes, content_map)}

You are trying to find Python objects that most satisfy the following requirement:
{requirement}

Output the index that matches the requirement the most. Start your answer with "Index:".
"""
    chat = Chat(user_message=prompt,
                system_message="You are a helpful assistant.")
    res = chat.complete_chat_expensive()
    res = res.split("Index:")[1].strip()
    matched_node = nodes[int(res)]
    return matched_node


def make_code_searcher(code_type: str, content_map: ContentMap = None):
    def code_searcher(root: Node, requirement):
        return code_beam_searcher(root, requirement, code_type, content_map)
    return code_searcher