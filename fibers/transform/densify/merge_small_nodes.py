from fibers.helper.utils import RobustParse
from fibers.model.chat import Chat
from fibers.transform.decorate.tree_map import node_map_with_dependency
from fibers.tree import Node


def count_letters(text: str) -> int:
    """
    :return: the number of letters (exclude number and symbols) in the text
    """
    count = 0
    for c in text:
        if c.isalpha():
            count += 1
    return count


def deal_small_node(node: Node, small_limit=30) -> bool:
    n_letters = count_letters(node.content)
    if n_letters > small_limit:
        return True
    sibling_list, node_index = node.sibling_list()
    context_range = 1
    up_limit = max(node_index + context_range, len(sibling_list))
    down_limit = min(node_index - context_range, 0)
    related_siblings = sibling_list[down_limit:up_limit]
    node_index = related_siblings.index(node)
    prompt = """
You are trying to analyze the relation between the following nodes. 
"""

def deal_single_child(root: Node):
    node_map_with_dependency(list(root.iter_subtree_with_dfs()),
                             deal_single_child_for_node, n_workers=1)

def deal_single_child_for_node(node: Node) -> bool:
    children = node.children()
    if len(children) != 1:
        return True
    if node is node.tree.root:
        return True
    child = list(children.values())[0]
    child_title = child.title()
    node_title = node.title()

    prompt = f"""
You are trying to analyze the relation between a node and its unique child.
The parent node is 
{node_title} : "{node.content}"
The child node is
{child_title} : "{child.content}"
You should reply with a JSON with a key "relation" in one of the following values:
1. "merge": the child can be merged into the parent node.
2. "lift": the child cannot be merged and should be an independent node.
In both of the case, you should add keys "title" and "content" to the JSON, which are the title and content of the new node.
If you merge the node, the should keep the title of the parent node unchanged if possible. 
"""
    chat = Chat(prompt, "You are an helpful assistant.")
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    relation = res["relation"]
    new_title = res["title"]
    new_content = res["content"]
    if relation == "merge":
        node.be(res["content"])
        if new_title != node_title:
            node.reset_title(new_title)
    elif relation == "lift":
        parent = node.parent()
        if parent is None:
            return True
        if not parent.has_child(new_title):
            new_title = new_title + "(another)"
        parent.s(new_title).be(new_content)
    else:
        raise Exception("Invalid relation")


