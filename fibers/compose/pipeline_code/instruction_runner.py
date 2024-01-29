from typing import List

from fibers.compose.decorate.code_summary import summarize_code_tree, \
    CodeSummarizedNodeClass
from fibers.compose.extract.code_searcher import make_code_searcher
from fibers.compose.utils_code.call_function import VariableTable, call_function_node
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.model.chat import Chat
from fibers.tree import Tree
from fibers.tree.node import ContentMap


class InstructionRunner:
    def __init__(self, module, variable_table=None):
        self.module = module
        self.variable_table = variable_table or VariableTable()
        self.tree = get_tree_for_module(module)
        summarize_code_tree(self.tree)
        content_map = ContentMap(
            lambda n: CodeSummarizedNodeClass.get_summary(n) or n.content)
        self.beam_searcher = make_code_searcher("function", content_map)

    def run_instructions(self, instructions):
        run_instructions(instructions, self.beam_searcher, self.tree, self.variable_table)


def make_function_requirement(instruction: str):
    prompt = f"""
Based on the following instruction, you should give a requirement of the function that you want to find. You should not add additional information in the requirement.

Instruction:
{instruction}

Start you answer with "The function".
"""
    res = Chat(user_message=prompt).complete_chat()
    return res


def run_instructions(instructions: List[str], beam_searcher, tree: Tree,
                     variable_table: VariableTable = None):
    var_table = variable_table or VariableTable()
    codes = []
    for instruction in instructions:
        print(instruction)
        requirement = make_function_requirement(instruction)
        print(requirement)
        nodes_related = beam_searcher(tree.root, requirement)
        code_for_inst = call_function_node(nodes_related, var_table, instruction)
        codes.append(code_for_inst)
        print("Variables:")
        print(var_table.get_prompt())
    return
