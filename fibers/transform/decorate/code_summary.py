import inspect

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.helper.cache.cache_service import cached_function, auto_cache
from fibers.model.chat import Chat
from fibers.transform.decorate.tree_map import node_map_with_dependency
from fibers.transform.utils_code.code_env import get_function_module_env
from fibers.tree import Node
from fibers.tree.node import NodeContentMap
from fibers.tree.node_class import CodeNodeClass, NodeClass
from fibers.tree.prompt_utils import get_node_list_prompt


class CodeSummarizedNodeClass(NodeClass):
    @staticmethod
    def set_summary(node: Node, summary: str, prefix="main"):
        node.add_class(CodeSummarizedNodeClass)
        CodeSummarizedNodeClass.set_attr(node, prefix + "_summary", summary)

    @staticmethod
    def get_summary(node: Node, prefix="main"):
        return CodeSummarizedNodeClass.get_attr(node, prefix + "_summary")

    @staticmethod
    def serialize(node: Node):
        return CodeSummarizedNodeClass.get_summary(node)


@auto_cache
def summarize_function(node: Node):
    """
    This function is to summarize code content.
    """
    function = CodeNodeClass.get_obj(node)
    function_src = inspect.getsource(function)
    function_env = get_function_module_env(node)
    prompt = f"""
You are required to summarize what the following function is doing into 30 words.
You are provided with the environment of the function for a better understanding, but you should not mention it in your summary. 

Function environment:
{function_env}

Function:
{function_src}

Start your answer with "Summary: The function"
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

    node_type = CodeNodeClass.get_type(node)
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
    if not node.is_empty:
        prompt += f"""
docstring:
{node_content}"""

    if len(children) > 0:
        children_list = get_node_list_prompt(children, NodeContentMap(
            title_map=lambda n: CodeNodeClass.get_type(n) + " " + n.title(),
            content_map=lambda n: CodeSummarizedNodeClass.get_summary(n)
        )
                                             )
        prompt += f"""
children:
{children_list}"""
    prompt += f"""

Start you summary with "Summary: The {node_type}" """
    chat = Chat(prompt, "You are a helpful assistant who help Python programmers")
    res = chat.complete_chat()
    res = res.replace("Summary: ", "")
    return res


def summarize_code_tree(node: Node) -> bool:
    # If the node is already summarized, return True
    if node.isinstance(CodeSummarizedNodeClass):
        return True
    module_tree_type = CodeNodeClass.get_type(node)
    if module_tree_type in ["module", "class", "section"]:
        # Check if all children are summarized
        children_all_summarized = True
        for key, item in node.children().items():
            if not item.isinstance(CodeSummarizedNodeClass):
                children_all_summarized = False
                break
        # If not all children are summarized, this round failed, need to return False
        if not children_all_summarized:
            return False
        # If all children are summarized, summarize the node
        else:
            summary = summary_children(node)
            CodeSummarizedNodeClass.set_summary(node, summary)
    # If the node is a function, ensure it is summarized
    elif module_tree_type == "function":
        if not node.isinstance(CodeSummarizedNodeClass):
            summary = summarize_function(node)
            CodeSummarizedNodeClass.set_summary(node, summary)
    # If the node is neither a function nor a container, skip it
    else:
        return True


@cached_function
def summary_needing_situation(node: Node):
    function = CodeNodeClass.get_obj(node)
    function_src = inspect.getsource(function)
    function_env = get_function_module_env(node)
    prompt = f"""
    You are required to summarize when the following function is needed in 15 words.
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
    return res


if __name__ == "__main__":
    from fibers import tree as tree_module
    from fibers.indexing.parent_mixed import ParentMixedIndexing

    tree = get_tree_for_module(tree_module)
    node_map_with_dependency(list(tree.iter_with_dfs())[:-1], summarize_code_tree)


    def get_summary(node: Node):
        if node.isinstance(CodeSummarizedNodeClass):
            return CodeSummarizedNodeClass.get_summary(node)
        else:
            return node.content

    content_map = NodeContentMap(get_summary)

    tree.show_tree_gui(content_map)

    from fibers.transform.extract.traverser import beam_search

    #nodes_related = beam_search(tree.root, "The function that adds children to a node", content_map)
    nodes_related = beam_search(tree.root, "The function that visualizes a tree",
                                content_map)
    nodes_related = [node for node in nodes_related if node.isinstance(CodeSummarizedNodeClass) and CodeNodeClass.get_type(node) == "function"]
    print(nodes_related)

    cache_service.save_used_cache()
