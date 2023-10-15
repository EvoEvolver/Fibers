from typing import List

from fibers.model.chat import Chat
from fibers.tree import Node


def pick_next(node: Node, requirement: str):
    children_in_prompt = []
    children = node.children()
    children_list = list(children.values())
    if len(children_list) == 0:
        return []
    children_i = 1
    for key, child in children.items():
        child_in_prompt = str(children_i) + ". " + key
        if not child.is_empty:
            child_in_prompt += " : " + child.content
        children_in_prompt.append(child_in_prompt)
        children_i += 1

    children_in_prompt = "\n".join(children_in_prompt)

    prompt = f"""
You are traveling on a tree of knowledge. You should pick children from the following list based on the requirement.

Children:
{children_in_prompt}

Requirement:
{requirement}

Format:
Output the indices of the children that satisfies the requirement, separated by commas. Start your answer with "Indices:".
"""
    chat = Chat(
        user_message=prompt)
    res = chat.complete_chat_expensive()
    indices = res.split(":")[1].strip()
    indices = indices.split(",")
    indices = [int(i.strip()) for i in indices]

    picked = []
    for i in indices:
        picked.append(children_list[i-1])
    related_nodes = picked[:]
    for child in picked:
        related_nodes.extend(pick_next(child, requirement))
    return related_nodes


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("dingzhen_world.json")
    related_nodes = pick_next(tree.root, "The children that possibly include the answer to the question: What is the main industrial of Ganzi? You must pick at least one child.")
    print(related_nodes)