import inspect

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.helper.cache.cache_service import cached_function, cache_service
from fibers.helper.utils import parallel_map
from fibers.model.chat import Chat
from fibers.tree import Tree, Node
from fibers.tree.node import NodeContentMap
from fibers.tree.node_class import CodeNodeClass, NodeClass


class CodeSummarizedNodeClass(NodeClass):
    @staticmethod
    def set_summary(node: Node, summary: str):
        node.add_class(CodeSummarizedNodeClass)
        CodeSummarizedNodeClass.set_attr(node, "summary", summary)

    @staticmethod
    def get_summary(node: Node):
        return CodeSummarizedNodeClass.get_attr(node, "summary")

    @staticmethod
    def serialize(node: Node):
        return CodeSummarizedNodeClass.get_summary(node)


@cached_function
def summarize_function(function_src: str, function_env: str):
    """
    This function is to summarize code content.
    """
    prompt = f"""
You are required to summarize what the following function is doing into 30 words.
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


def get_function_env(function_node: Node):
    parent_nodes = [function_node.parent()]
    while True:
        last_parent = parent_nodes[-1]
        parent_nodes.append(last_parent.parent())
        if CodeNodeClass.get_type(last_parent) == "module":
            break
    parent_nodes = parent_nodes[::-1]
    res = []
    for i, node in enumerate(parent_nodes):
        res.append(">" * i + CodeNodeClass.get_type(node) + ":" + node.title())
    return "\n".join(res)


def summarize_functions_on_tree(tree: Tree):
    function_nodes = []
    function_srcs = []
    function_envs = []
    for node in tree.all_nodes():
        if node.isinstance(CodeNodeClass) and CodeNodeClass.get_type(node) == "function":
            function = CodeNodeClass.get_obj(node)
            function_nodes.append(node)
            function_srcs.append(inspect.getsource(function))
            function_envs.append(get_function_env(node))

    for i, summary in parallel_map(summarize_function, function_srcs, function_envs):
        node = function_nodes[i]
        CodeSummarizedNodeClass.set_summary(node, summary)

@cached_function
def summary_children(node: Node):
    children = []
    children_title = []
    node_name = node.title()
    node_content = node.content
    if len(node.children()) == 0:
        return "This node has no children"
    else:
        for key, item in node.children().items():
            children.append(item)
            children_title.append(key)


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
        prompt += f"""
children:"""
        for child, title in zip(children, children_title):
            prompt += f"""
{CodeNodeClass.get_type(child)} {title}: {CodeSummarizedNodeClass.get_summary(child)}"""

    prompt += f"""

Start you summary with "Summary: The {node_type}" """
    chat = Chat(prompt, "You are a helpful assistant who help Python programmers")
    res = chat.complete_chat()
    res = res.replace("Summary: ", "")
    return res


def summarize_containers_on_tree_one_round(tree: Tree) -> bool:
    """
    Summarize module, class, and section on the tree
    """
    node_to_summarize = []
    has_node_to_summarize = False
    all_nodes = list(tree.iter_with_dfs())[:-1]
    for node in all_nodes:
        if not node.isinstance(CodeSummarizedNodeClass):
            has_node_to_summarize = True
        else:
            continue
        module_tree_type = CodeNodeClass.get_type(node)
        if module_tree_type in ["module", "class", "section"]:
            children_all_summarized = True
            for key, item in node.children().items():
                if not item.isinstance(CodeSummarizedNodeClass):
                    children_all_summarized = False
                    break
            if not children_all_summarized:
                continue
            node_to_summarize.append(node)
        elif module_tree_type == "function":
            if not node.isinstance(CodeSummarizedNodeClass):
                raise ValueError(f"Code summary not found for {node.title()}")
        else:
            continue

    if len(node_to_summarize) > 0:
        for i, summary in parallel_map(summary_children, node_to_summarize):
            CodeSummarizedNodeClass.set_summary(node_to_summarize[i], summary)

    return has_node_to_summarize

def summarize_containers_on_tree(tree: Tree):
    while summarize_containers_on_tree_one_round(tree):
        pass

if __name__ == "__main__":
    from fibers import tree as tree_module

    tree = get_tree_for_module(tree_module)
    summarize_functions_on_tree(tree)

    summarize_containers_on_tree(tree)

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
