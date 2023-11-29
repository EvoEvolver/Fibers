from typing import Callable

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.model.chat import Chat

from fibers.transform.decorate.code_summary import CodeSummarizedNodeClass, \
    summarize_code_tree
from fibers.transform.utils_code.header import get_function_header
from fibers.tree import Node
from fibers.tree.node_class import CodeNodeClass
from asteval import Interpreter

class VariableTable:
    def __init__(self):
        self.variable_objs = {}
        self.variable_docs = {}

    def add_variable(self, name, obj, docs):
        self.variable_objs[name] = obj
        self.variable_docs[name] = docs

    def get_variable(self, name):
        return self.variable_objs[name], self.variable_docs[name]

    def get_prompt(self):
        prompt_list = []
        for name, docs in self.variable_docs.items():
            prompt_list.append(f"{name}: {docs}")
        return "\n".join(prompt_list)

    def is_empty(self):
        return len(self.variable_objs) == 0

    def get_interpreter(self):
        interpreter = Interpreter()
        for name, obj in self.variable_objs.items():
            interpreter.symtable[name] = obj
        return interpreter

def call_function_node(node: Node, vars_table: VariableTable, requirement: str):
    func = CodeNodeClass.get_obj(node)
    func_header = get_function_header(func)

    prompt = f"""
You are required to call the following function to meet the requirement:

Function header:
{func_header}
"""
    if node.isinstance(CodeSummarizedNodeClass):
        summary = CodeSummarizedNodeClass.get_summary(node)
        prompt += f"""
Function summary:
{summary}
"""
    prompt += f"""
Requirement:
{requirement}
    
You are required to output a Python dict of the following format:"""
    prompt += """
{
    "variable_name": <name of the variable for storing the result>,
    "variable_docs": <documentation of the variable for better understanding of others>,
    "args": <a list of arguments>,
    "kwargs": <a dict of keyword arguments>
}"""
    prompt += """
Please refer to the function header for a correct format of the arguments.
"""
    if not vars_table.is_empty():
        prompt += f"""
You can use the following variables for the arguments:
{vars_table.get_prompt()}
"""
    chat = Chat(prompt, "You are a helpful assistant who call Python functions")
    res = chat.complete_chat()
    exec_function(func, res, vars_table)
    print(prompt)
    return vars_table

def exec_function(func: Callable, caller_dict_str: str, vars_table: VariableTable):
    interpreter = vars_table.get_interpreter()
    caller_dict = interpreter(caller_dict_str)
    args = caller_dict["args"]
    kwargs = caller_dict["kwargs"]
    return_value = func(*args, **kwargs)
    vars_table.add_variable(caller_dict["variable_name"], return_value, caller_dict["variable_docs"])

def example():
    from fibers.testing.testing_modules.v_lab import operation
    tree = get_tree_for_module(operation)
    summarize_code_tree(tree)
    node = tree.get_node_by_path(('fibers.testing.testing_modules.v_lab.operation',
                                  'Operations', 'Salt water making',
                                  'get_a_beaker_of_salt_water',
                                  'get_a_beaker_of_salt_water'))
    variables = VariableTable()
    variables.add_variable("water_volume", 1000, "The volume of water in the beaker.")
    available_vars = call_function_node(node, variables,
                                        "the water volume should be water_volume, salt volume is 10. name the returned beaker as zijian_water")
    print(available_vars.get_prompt())


if __name__ == '__main__':
    example()
