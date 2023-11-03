from typing import List

from fibers.tree import Node, Tree
from fibers.tree.node import ContentMap

"""
# Represent nodes in prompt
"""

def get_node_list_prompt(nodes: List[Node], content_map: ContentMap = None):
    if content_map is None:
        content_map = ContentMap()
    prompt = []
    for i, node in enumerate(nodes):
        title, content = content_map.get_title_and_content(node)
        prompt.append(f"{i}. {title}: {content}")
    prompt = "\n".join(prompt)
    return prompt


"""
# Represent tree in prompt
"""


def get_tree_dict(tree: Tree, add_index=True):
    tree_dict = {
        "subtopics": {},
    }
    nodes = tree.all_nodes()
    node_indexed = []
    i_node = 0
    for i, node in enumerate(nodes):
        node_path = tree.get_node_path(node)
        leaf = tree_dict
        for key in node_path:
            if key not in leaf["subtopics"]:
                leaf["subtopics"][key] = {"subtopics": {}}
            leaf = leaf["subtopics"][key]
        if len(node.content) > 0:
            leaf["content"] = node.content
            if add_index:
                leaf["index"] = i_node
            node_indexed.append(node)
            i_node += 1
    return tree_dict, node_indexed


def get_dict_for_prompt(tree: Tree):
    dict_without_indices, node_indexed = get_tree_dict(tree, add_index=False)
    delete_extra_keys_for_prompt(dict_without_indices)
    return dict_without_indices


def get_path_content_str_for_prompt(tree: Tree):
    res = []
    for node, path in tree.node_path.items():
        if len(node.content) == 0:
            continue
        path_str = "/".join(path)
        if len(path) == 0:
            path_str = "root"
        res.append(f"{path_str}: {node.content}")
    return "\n".join(res)


def get_dict_with_indices_for_prompt(tree: Tree):
    dict_with_indices, node_indexed = get_tree_dict(tree)
    delete_extra_keys_for_prompt(dict_with_indices)
    return dict_with_indices, node_indexed


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
