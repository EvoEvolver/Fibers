from typing import List

from fibers.tree import Node
from fibers.tree.node import NodeMap

"""
# Represent nodes in prompt
"""

def get_node_list_prompt(nodes: List[Node], node_map: NodeMap = None):
    if node_map is None:
        node_map = NodeMap()
    prompt = []
    for i, node in enumerate(nodes):
        title, content = node_map.get_title_and_content(node)
        prompt.append(f"{i}. {title}: {content}")
    prompt = "\n".join(prompt)
    return prompt


"""
# Represent tree in prompt
"""


def delete_extra_keys_for_prompt(tree):
    for key, leaf in tree["subtopics"].items():
        delete_extra_keys_for_prompt(leaf)
    if "content" not in tree:
        for key, leaf in tree["subtopics"].items():
            tree[key] = leaf
        del tree["subtopics"]
    else:
        if len(tree["subtopics"]) == 0:
            del tree["subtopics"]
        if len(tree["content"]) == 0:
            del tree["content"]
