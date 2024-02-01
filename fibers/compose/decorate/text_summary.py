from fibers.data_loader.bad_text_node_class import BadTextNodeClass
from fibers.helper.cache.cache_service import auto_cache
from fibers.model.chat import Chat
from fibers.compose.decorate.tree_map import node_map_with_dependency
from fibers.tree import Node
from fibers.tree.node import ContentMap
from fibers.tree.node_class import NodeClass
from fibers.tree.prompt_utils import get_node_list_prompt

class TextSummaryNode(NodeClass):
    @classmethod
    def render(cls, node: Node, rendered):
        rendered.tabs["text_summary"] = TextSummaryNode.get_attr(node, "text_summary")


def set_content_summary(root: Node, requirement=""):
    @auto_cache
    def summary(node: Node):
        return summarize_text_node(node, requirement)
    node_map_with_dependency(list(root.iter_subtree_with_dfs()),
                             summary)


@auto_cache
def summarize_text_node(node: Node, requirement) -> bool:
    for child in node.children().values():
        if not child.isinstance(TextSummaryNode):
            return False

    content_map = ContentMap(lambda node: TextSummaryNode.get_attr(node, "text_summary"))
    children_prompt = get_node_list_prompt(list(node.children().values()), content_map)
    prompt = f"""
You are trying to summarize the content of a part of an article. The summary should be a shortened version of the content of the it."""
    if not node.is_empty():
        prompt += f"""
Content:
{node.content}"""
    if node.has_child():
        prompt+= f"""
Sub-sections:
{children_prompt}"""
    prompt += f"""
Based on the information above, output your summary. 
{requirement}
The summary should be in the format of a HTML ordered list.
Start your answer with `<ol>`.
"""
    chat = Chat(prompt,
                "You are an helpful assistant who help organize knowledge.")
    res = chat.complete_chat()
    #res = res[len("Summary:"):].strip()

    TextSummaryNode.set_attr(node, "text_summary", res)

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
