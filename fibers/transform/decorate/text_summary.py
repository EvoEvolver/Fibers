from typing import List

from fibers.data_loader.bad_text_node_class import BadTextNodeClass
from fibers.helper.cache.cache_service import cached_function
from fibers.helper.utils import RobustParse, standard_multi_attempts, parallel_map
from fibers.model.chat import Chat
from fibers.transform.utils_text.node_env_prompt import get_node_env_for_prompt
from fibers.tree import Node


@cached_function
def children_summarize(node_env_prompt):
    prompt = node_env_prompt + f"""Based on the information above, output a JSON dict with `summary` for the node."""
    chat = Chat(prompt,
                "You are an helpful assistant who help organize knowledge and only output in JSON.")
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    return res



@cached_function
def make_title_by_content(content):
    prompt = f"""
Summarize the following content into a short summary that is no longer than 10 words.
{content}
Start you answer with `Summary:`.
"""
    chat = Chat(prompt, "You are an helpful assistant who help organize knowledge.")
    res = chat.complete_chat()
    res = res[len("Summary:"):].strip()
    return res


def reset_bad_titles(nodes):
    bad_title_nodes = []
    node_contents = []
    for node in nodes:
        if BadTextNodeClass.has_bad_reason(node, "bad_title"):
            node_contents.append(node.content)
            bad_title_nodes.append(node)
    for i, title in parallel_map(make_title_by_content, node_contents):
        node = bad_title_nodes[i]
        node.reset_title(title, overlap=True)


def add_children_summary(nodes: List[Node]) -> (List[Node], List[str]):
    non_empty_nodes = []
    node_envs = []
    for node in nodes:
        if node.content.strip() != "":
            continue
        node_env_prompt = get_node_env_for_prompt(node,
                                                  "You are trying to summarize the content of a part of a knowledge base. The summary should be a shortened version of the content of the children and the node itself.")
        node_envs.append(node_env_prompt)
        non_empty_nodes.append(node)

    summary_list = []
    for i, summary in parallel_map(children_summarize, node_envs):
        summary_list.append(summary["summary"])

    return non_empty_nodes, summary_list
