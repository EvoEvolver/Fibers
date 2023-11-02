from typing import List

from fibers.helper.utils import RobustParse
from fibers.model.chat import Chat
from fibers.tree import Node
from fibers.tree.node import NodeContentMap


def beam_search(root: Node, requirement: str, content_map: NodeContentMap = NodeContentMap()) -> List[Node]:
    node_queue = [root]
    visited_nodes = set()
    matched_nodes_set = set()
    while len(node_queue) > 0:
        node = node_queue.pop(0)
        print(node.path())
        matched_nodes, possible_ancestors = pick_next(node,
                                                      requirement,
                                                      content_map)
        matched_nodes_set.update(matched_nodes)
        for node in possible_ancestors + matched_nodes:
            if node not in visited_nodes:
                node_queue.append(node)
                visited_nodes.add(node)

    return list(matched_nodes_set)


def pick_next(node: Node, requirement: str, content_map: NodeContentMap = NodeContentMap()) -> (List[Node], List[Node]):
    children_in_prompt = []
    children = node.children()
    children_list = list(children.values())
    if len(children_list) == 0:
        return [], []
    children_i = 1
    for key, child in children.items():
        title, content = content_map.get_title_and_content(child)
        child_in_prompt = str(children_i) + ". " + title
        if len(content)>0:
            child_in_prompt += " : " + content
        children_in_prompt.append(child_in_prompt)
        children_i += 1

    children_in_prompt = "\n".join(children_in_prompt)

    prompt = f"""
You are traveling on a tree of knowledge. From the following list, you should pick the children that satisfies the requirement, and the children might be the ancestor of the required node.

Children:
{children_in_prompt}

Requirement:
{requirement}

Format:
Output a JSON dict with key "matched_indices" for a list of indices of the children that satisfies the requirement, and key "ancestor_indices" for a list of indices that might be the ancestor of the required node.
Your output must contain these two keys.
You should order the indices by their relevance to the requirement.
"""
    chat = Chat(user_message=prompt,
                system_message="You are a helpful assistant for arranging knowledge. You should output merely JSON.")
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    matched_indices = res["matched_indices"]
    ancestor_indices = res["ancestor_indices"]
    matched_children = [children_list[i - 1] for i in matched_indices]
    ancestor_children = [children_list[i - 1] for i in ancestor_indices]
    return matched_children, ancestor_children


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree

    tree = load_sample_tree("dingzhen_world.json")
    matched_children, ancestor_children = pick_next(tree.root,
                              "The children that include the answer to the question: What is the main industrial of Ganzi? You must pick at least one child.")
    print(matched_children)
    print(ancestor_children)
