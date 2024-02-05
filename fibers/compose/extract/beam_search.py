from typing import List

from fibers.helper.utils import RobustParse, parallel_map
from fibers.model.chat import Chat
from fibers.tree import Node
from fibers.tree.node import ContentMap
from fibers.tree.prompt_utils import get_node_list_prompt


def beam_search(root: Node, requirement: str, content_map: ContentMap = None) -> List[
    Node]:
    node_queue = [root]
    visited_nodes = set()
    matched_nodes_set = set()

    def pick_next_wrapped(node: Node):
        return pick_next_CoT(node, requirement, content_map)

    while len(node_queue) > 0:
        node_touched = []
        for i, res in parallel_map(pick_next_wrapped, node_queue):
            matched_nodes, possible_parents = res
            matched_nodes_set.update(matched_nodes)
            node_touched.extend(possible_parents)
            node_touched.extend(matched_nodes)
        node_queue = []
        for node in node_touched:
            if node not in visited_nodes:
                node_queue.append(node)
                visited_nodes.add(node)
    return list(matched_nodes_set)


def pick_next(node: Node, requirement: str, content_map: ContentMap = None) -> (
        List[Node], List[Node]):
    if content_map is None:
        content_map = ContentMap()
    children = node.children()
    children_list = list(children.values())
    if len(children_list) == 0:
        return [], []

    if len(children_list) == 1:
        return [children_list[0]], []

    children_in_prompt = get_node_list_prompt(children_list, content_map)

    prompt = f"""
You are traveling on a tree of knowledge. From the following list, you should pick the children that satisfies the requirement, and the children might be the ancestor of the required node.

Children:
{children_in_prompt}

Requirement:
{requirement}

Format:
Output a JSON dict with key "matched_indices" for a list of indices of the children that satisfies the requirement, and key "parent_indices" for a list of indices that might be the ancestor of the required node.
"""
    chat = Chat(user_message=prompt,
                system_message="You are a helpful assistant for arranging knowledge. You should output merely JSON.")
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    matched_indices = res["matched_indices"] if "matched_indices" in res else []
    parent_indices = res["parent_indices"] if "parent_indices" in res else []
    matched_children = [children_list[i] for i in matched_indices]
    parent_indices = [children_list[i] for i in parent_indices]
    return matched_children, parent_indices


def pick_next_CoT(node: Node, requirement: str, content_map: ContentMap = None) -> (
        List[Node], List[Node]):
    if content_map is None:
        content_map = ContentMap()
    children = node.children()
    children_list = list(children.values())
    if len(children_list) == 0:
        return [], []

    if len(children_list) == 1:
        return [children_list[0]], []

    children_in_prompt = get_node_list_prompt(children_list, content_map)

    prompt = f"""
You are traveling on a tree of knowledge. From the following list, you should pick the children that satisfies the requirement, and the children might be the ancestor of the required node.

Children:
{children_in_prompt}

Requirement:
{requirement}

Format:
Output a JSON list with items being a dict for the corresponding child. The dict should has three keys: "index" for the index of the child, "analysis" for a short analysis for whether the child satisfies the requirement, and key "matched" for a boolean value indicating the result.
"""
    chat = Chat(user_message=prompt,
                system_message="You are a helpful assistant for arranging knowledge. You should output merely JSON.")
    res = chat.complete_chat()
    res = RobustParse.list(res)
    print(chat)
    matched_children = []
    for i, item in enumerate(res):
        if item["matched"]:
            matched_children.append(children_list[i])
    return matched_children, []


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree

    tree = load_sample_tree("dingzhen_world.json")
    matched_children, ancestor_children = pick_next(tree.root,
                                                    "The children that include the answer to the question: What is the main industrial of Ganzi? You must pick at least one child.")
    print(matched_children)
    print(ancestor_children)
