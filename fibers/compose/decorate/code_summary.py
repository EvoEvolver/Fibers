import inspect

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.helper.cache.cache_service import cached_function, auto_cache, caching
from fibers.helper.utils import parallel_map
from fibers.model.chat import Chat
from fibers.compose.decorate.tree_map import node_map_with_dependency
from fibers.compose.utils_code.code_env import get_function_module_env
from fibers.tree import Node, Tree
from fibers.tree.node import ContentMap
from fibers.tree.node_attr import Attr
from fibers.tree.node_class import CodeData
from fibers.tree.node_class.code_node import get_obj, get_type
from fibers.tree.prompt_utils import get_node_list_prompt


class CodeSummary(Attr):
    def __init__(self, node: Node):
        super().__init__(node)
        self.summary = None

    @staticmethod
    def set_summary(node: Node, summary: str):
        node.get_attr(CodeSummary).summary = summary

    @staticmethod
    def get_summary(node: Node):
        if not node.has_attr(CodeSummary):
            return None
        return node.get_attr(CodeSummary).summary

    @staticmethod
    def serialize(node: Node):
        return CodeSummary.get_summary(node)

    def render(self, node: Node, rendered):
        if self.summary is not None:
            rendered.tabs["summary"] = self.summary


@auto_cache
def summarize_function(node: Node):
    """
    This function is to summarize code content.
    """
    function = get_obj(node)
    function_src = inspect.getsource(function)
    function_env = get_function_module_env(node)
    prompt = f"""
You are required to summarize what the following function is doing into 30 words.
You are provided with the environment of the function for a better understanding, but you should not mention it in your summary. 

Function environment:
{function_env}

Function:
{function_src}

Without mentioning the function name, start your answer with "Summary: The function" 
"""
    chat = Chat(prompt, "You are a helpful assistant who help Python programmers")
    res = chat.complete_chat()
    res = res.replace("Summary: ", "")
    return res


@auto_cache
def summary_children(node: Node):
    children = list(node.children().values())
    node_name = node.title()
    node_content = node.content

    node_type = get_type(node)
    prompt = f"""
You are summarizing the content of the following {node_type} in Python for documentation.
You should consider the name, type and content of the {node_type} when summarizing.
You summary should be no more than 40 words.
"""
    if node_type == "section":
        prompt += f"""
A section is a collection of modules, classes and functions with a common theme.
"""

    prompt += f"""
{node_type} name: {node_name}
"""
    if not node.is_empty():
        prompt += f"""
docstring:
{node_content}"""

    if len(children) > 0:
        children_list = get_node_list_prompt(children, ContentMap(
            title_map=lambda n: get_type(n) + " " + n.title(),
            content_map=lambda n: CodeSummary.get_summary(n)
        )
                                             )
        prompt += f"""
children:
{children_list}"""
    prompt += f"""

Without mentioning the {node_type} name, start you summary with "Summary: The {node_type}" """
    chat = Chat(prompt, "You are a helpful assistant who help Python programmers")
    res = chat.complete_chat()
    res = res.replace("Summary: ", "")
    return res


def summarize_code_node(node: Node) -> bool:
    # If the node is already summarized, return True
    if node.has_attr(CodeSummary):
        return True
    if not node.has_attr(CodeData):
        return True
    module_tree_type = get_type(node)
    if module_tree_type in ["module", "class", "section"]:
        # Check if all children are summarized
        children_all_summarized = True
        for key, item in node.children().items():
            # ignore the non-code node
            # TODO: consider the README node too
            if get_type(item) == "document":
                continue
            if not item.has_attr(CodeSummary):
                children_all_summarized = False
                break
        # If not all children are summarized, this round failed, need to return False
        if not children_all_summarized:
            return False
        # If all children are summarized, summarize the node
        else:
            summary = summary_children(node)
            CodeSummary.set_summary(node, summary)
            return True
    # If the node is a function, ensure it is summarized
    elif module_tree_type == "function":
        if not node.has_attr(CodeSummary):
            summary = summarize_function(node)
            CodeSummary.set_summary(node, summary)
            return True
    # If the node is neither a function nor a container, skip it
    else:
        return True


@auto_cache
def summary_needing_situation_0(node: Node):
    module_tree_type = get_type(node)
    if module_tree_type != "function":
        return
    function = get_obj(node)
    function_src = inspect.getsource(function)
    function_env = get_function_module_env(node)
    prompt = f"""
    You are required to summarize when the following function is needed in 30 words.
    You are provided with the environment of the function for a better understanding, but you should not mention it in your summary. 
    """
    prompt += f"""
    Function environment:
    {function_env}

    Function:
    {function_src}

    Start your answer with "Summary: The function"
    """
    chat = Chat(prompt, "You are a helpful assistant who help Python programmers")
    res = chat.complete_chat()
    res = res.replace("Summary: ", "")
    CodeSummary.set_summary(node, res)

@auto_cache
def summary_needing_situation(node: Node):
    module_tree_type = get_type(node)
    if module_tree_type != "function":
        return
    function = get_obj(node)
    function_src = inspect.getsource(function)
    prompt = f"""
    You are required to summarize when the following function is needed in 30 words.
    You should not add any information beyond the function signature, docstring and the function body.
    """
    prompt += f"""
    Function:
    {function_src}

    Start your answer with "Summary: The function"
    """
    chat = Chat(prompt, "You are a helpful assistant who help Python programmers")
    res = chat.complete_chat()
    res = res.replace("Summary: ", "")
    CodeSummary.set_summary(node, res)

def summarize_code_tree(tree: Tree):
    node_map_with_dependency(list(tree.iter_with_dfs())[:-1], summarize_code_node)


def summarize_function_for_needing_situation(tree: Tree):
    parallel_map(summary_needing_situation, list(tree.iter_with_dfs())[:-1])


if __name__ == "__main__":
    from moduler import core
    tree = get_tree_for_module(core)
    summarize_code_tree(tree)
    tree.show_tree_gui_react()
    caching.save_used()

