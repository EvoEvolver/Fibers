from fibers.data_loader.bad_text_node_class import BadTextNodeClass
from fibers.helper.cache.cache_service import auto_cache
from fibers.model.chat import Chat
from fibers.transform.decorate.tree_map import node_map_with_dependency
from fibers.tree import Node
from fibers.tree.prompt_utils import get_node_list_prompt


def set_children_summary(root: Node):
    node_map_with_dependency(list(root.iter_subtree_with_dfs()),
                             set_children_summary_for_node)


@auto_cache
def set_children_summary_for_node(node: Node) -> bool:
    if node.content.strip() != "" or len(node.children()) == 0:
        return True
    for child in node.children().values():
        if child.is_empty():
            return False
    children_prompt = get_node_list_prompt(list(node.children().values()))
    prompt = f"""
You are trying to summarize the content of a part of a knowledge base. The summary should be a shortened version of the content of the children.

Children:
{children_prompt}

Based on the information above, output your summary. Start your answer with `Summary:`.
"""
    chat = Chat(prompt,
                "You are an helpful assistant who help organize knowledge.")
    res = chat.complete_chat()
    res = res[len("Summary:"):].strip()
    node.be(res)
    return True


def reset_bad_titles(root: Node):
    node_map_with_dependency(list(root.iter_subtree_with_dfs()),
                             make_title_by_content)


@auto_cache
def make_title_by_content(node: Node) -> bool:
    if not BadTextNodeClass.has_bad_reason(node, "bad_title"):
        return True
    prompt = f"""
Summarize the following content into a short summary that is no longer than 10 words.
{node.content}
Start you answer with `Summary:`.
"""
    chat = Chat(prompt, "You are an helpful assistant who help organize knowledge.")
    res = chat.complete_chat()
    title = res[len("Summary:"):].strip()
    node.reset_title(title, overlap=True)
    return True
