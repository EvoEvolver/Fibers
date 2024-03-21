from typing import List


from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.gui.renderer import Rendered
from fibers.helper.utils import RobustParse, parallel_map
from fibers.indexing.indexing import VectorIndexing
from mllm.chat import Chat
from fibers.tree import Node
from fibers.tree.node_attr import Attr
from fibers.tree.node_attr.code_node import CodeData
from fibers.utils.code_process import get_function_header


class CodeIndexData(Attr):
    def __init__(self, node: Node, indexing):
        super().__init__(node)
        self.indexing: List[str] = indexing

    def render(self, node, rendered: Rendered):
        res = "<br/>".join(self.indexing)
        res = f"Code Indexing: {res}"
        rendered.tabs["Code Indexing"] = res


def get_code_indexing(root: Node) -> VectorIndexing:
    nodes = list(root.iter_subtree_with_dfs())
    for i, res in parallel_map(gen_code_indexing, nodes):
        if res is None:
            continue
        CodeIndexData(nodes[i], res)

    def get_weighted_contents(node):
        if not node.has_attr(CodeIndexData):
            return []
        indexings = CodeIndexData.get(node).indexing
        weight = 1 / len(indexings)
        return [(index, weight) for index in indexings]

    return VectorIndexing(nodes, get_weighted_contents)


def gen_code_indexing(node: Node):
    if not node.has_attr(CodeData):
        return
    code_data = CodeData.get(node)
    if code_data.module_tree_type != "function":
        return
    header = get_function_header(code_data.module_tree_obj)
    if header.strip() == "":
        return
    indexing = break_into_key_sentences(header)
    return indexing



def break_into_key_sentences(func_code: str) -> List[str]:
    prompt = \
        f"""
You are trying to generate some sentences that characterize the code and help others to find it.
The sentences should together cover the following aspects:
- the function name
- what the function does
- what the function is for
- the arguments
- the return value of the function

The code is:
<code start>
{func_code}
<code end>

Output your result as a JSON list of strings. All the strings should start with "The function"
"""
    chat = Chat(
        system_message="You are a smart summarizer of codes who only output in JSON format.")
    chat.add_user_message(prompt)
    res = chat.complete(expensive=True, cache=True)
    res = RobustParse.list(res)
    return res


if __name__ == '__main__':
    import q_lab

    root = get_tree_for_module(q_lab)
    indexing = get_code_indexing(root)
    res = indexing.get_top_k_nodes(["The function plots x y figure"],
                                   5)
    print(res)
