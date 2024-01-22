from typing import List

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.helper.cache.cache_service import caching
from fibers.model.chat import Chat
from fibers.compose.decorate.code_summary import CodeSummarizedNodeClass, \
    summarize_code_tree
from fibers.compose.extract.code_searcher import code_beam_searcher, make_code_searcher
from fibers.compose.utils_code.call_function import VariableTable, call_function_node
from fibers.tree import Tree
from fibers.tree.node import ContentMap


def make_function_requirement(instruction: str):
    prompt = f"""
Based on the following instruction, you should give a requirement of the function that you want to find. You should not add additional information in the requirement. Give an emphasis on what arguments the function should have.

Instruction:
{instruction}

Start you answer with "The function".
"""
    res = Chat(user_message=prompt).complete_chat()
    return res

def run_instructions(instructions: List[str], beam_searcher, tree: Tree):
    var_table = VariableTable()
    for instruction in instructions:
        print(instruction)
        requirement = make_function_requirement(instruction)
        print(requirement)
        node_related = beam_searcher(tree.root, requirement)
        call_function_node(node_related, var_table, instruction)
        print("Variables:")
        print(var_table.get_prompt())
    return

def main():
    import data_analyst

    tree = get_tree_for_module(data_analyst)

    summarize_code_tree(tree)

    content_map = ContentMap(
        lambda n: CodeSummarizedNodeClass.get_summary(n) or n.content)

    beam_searcher = make_code_searcher("function", content_map)

    instruction_list = [
        "Generate data with noise scale being 0.01",
        "Plot the data"
    ]

    run_instructions(instruction_list, beam_searcher, tree)
    caching.save_used()


if __name__ == '__main__':
    main()