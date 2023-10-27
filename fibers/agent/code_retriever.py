from typing import List

from fibers.agent import Agent
from fibers.helper.utils import RobustParse
from fibers.indexing.code import CodeIndexing
from fibers.model.chat import Chat
from fibers.tree import Tree, Node


class CodeRetriever(Agent):
    def __init__(self, module_tree: Tree):
        super().__init__()
        self.module_tree = module_tree
        self.indexing = CodeIndexing(module_tree)

    def get_function(self, description) -> List[Node]:
        imagined_signature = possible_signature(description)
        top_k_nodes = self.indexing.get_top_k_nodes(imagined_signature, k=3)
        return top_k_nodes


system_message = "You should output everything concisely as if you are a computer program"


def possible_signature(description: str):
    prompt = """
You are asked to imagine the signature of a function based on a description. You output should be in the form of:
{
"name": "...",
"docstring": "...",
"parameters": 
{"param_name": "param_description",
 ...}
}
"""
    chat = Chat(user_message=prompt, system_message=system_message)
    chat.add_user_message("Description:\n" + description)
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    return res


if __name__ == "__main__":
    from fibers.testing.testing_modules import v_lab
    from fibers.data_loader.module_to_tree import get_tree_for_module

    agent = CodeRetriever(get_tree_for_module(v_lab))
    nodes = agent.get_function("get a beaker of salt water")
    Tree.from_nodes(nodes).show_tree_gui()

