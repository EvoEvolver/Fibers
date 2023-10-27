from typing import List

from fibers.helper.cache.cache_service import cached_function
from fibers.helper.utils import RobustParse, multi_attempts, parallel_map
from fibers.model.chat import Chat
from fibers.transform.utils_text.node_env_prompt import get_node_env_for_prompt
from fibers.tree import Node


@multi_attempts
@cached_function
def children_summarize(node_env_prompt):
    prompt = node_env_prompt + f"""Based on the information above, output a JSON dict with `summary` for the node."""
    chat = Chat(prompt,
                "You are an helpful assistant who help organize knowledge and only output in JSON.")
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    return res


@multi_attempts
@cached_function
def make_title_by_content(content):
    prompt = f"""
Summarize the following content into a short summary that is no longer than 10 words.
Start you answer with `Summary:`.
"""
    chat = Chat(prompt, "You are an helpful assistant who help organize knowledge.")
    res = chat.complete_chat()
    res = res[len("Summary:"):].strip()
    return res


def reset_bad_titles(nodes) -> List[Node]:
    bad_title_nodes = []
    node_contents = []
    for node in nodes:
        if node.meta.get("bad_title", False):
            node_contents.append(node.content)
            bad_title_nodes.append(node)
    for i, title in parallel_map(make_title_by_content, node_contents):
        node = bad_title_nodes[i]
        node.reset_title(title)

    return bad_title_nodes


def add_children_summary(nodes) -> List[Node]:
    non_empty_nodes = []
    node_envs = []
    for node in nodes:
        if node.content.strip() != "":
            continue
        node_env_prompt = get_node_env_for_prompt(node,
                                                  "You are trying to summarize the children of a node in a tree knowledge base.")
        node_envs.append(node_env_prompt)
        non_empty_nodes.append(node)
    for i, summary in parallel_map(children_summarize, node_envs):
        node = non_empty_nodes[i]
        node.meta["children_summary"] = summary["summary"]

    return non_empty_nodes
