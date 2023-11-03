from typing import List

from fibers.tree import Node
from fibers.tree.node import NodeContentMap


def get_node_list_prompt(nodes: List[Node], content_map: NodeContentMap = None):
    if content_map is None:
        content_map = NodeContentMap()
    prompt = []
    for i, node in enumerate(nodes):
        title, content = content_map.get_title_and_content(node)
        prompt.append(f"{i}. {title}: {content}")
    prompt = "\n".join(prompt)
    return prompt
