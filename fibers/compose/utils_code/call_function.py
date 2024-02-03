from typing import List

import numpy

from fibers.helper.utils import standard_multi_attempts
from fibers.tree.node_class.code_node import get_obj
from moduler.decorator import example

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.model.chat import Chat

from fibers.compose.decorate.code_summary import CodeSummary, \
    summarize_code_tree
from fibers.compose.utils_code.header import get_function_header
from fibers.tree import Node
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
            value = self.variable_objs[name]
            prompt_list.append(f"{name}: {docs}. Value: {get_value_in_prompt(value)}")
        return "\n".join(prompt_list)

    def is_empty(self):
        return len(self.variable_objs) == 0

    def get_interpreter(self):
        interpreter = Interpreter()
        for name, obj in self.variable_objs.items():
            interpreter.symtable[name] = obj
        return interpreter


def get_value_in_prompt(value):
    long_limit = 3
    if isinstance(value, int) or isinstance(value, float):
        return str(value)
    elif isinstance(value, str):
        return f"'{value}'"
    elif isinstance(value, tuple) or isinstance(value, list):
        res = "[" if isinstance(value, list) else "("
        if len(value) > long_limit:
            res += get_value_in_prompt(value[0]) + ", " + get_value_in_prompt(
                value[1]) + ", ..."
            res += ", " + get_value_in_prompt(value[-1])
        else:
            res += ", ".join([get_value_in_prompt(v) for v in value])
        res += "]" if isinstance(value, list) else ")"
        return res
    elif isinstance(value, dict):
        res = "{"
        dict_kv_list = [f"{k}: {get_value_in_prompt(v)}" for k, v in value.items()]
        if len(dict_kv_list) > long_limit:
            res += ", ".join(dict_kv_list[:long_limit])
            res += ", ..."
            res += ", ".join(dict_kv_list[-1])
        else:
            res += ", ".join(dict_kv_list)
        res += "}"
        return res
    elif isinstance(value, numpy.ndarray):
        repr_str, classname = get_truncated_repr(value)
        shape = value.shape
        return f"{repr_str} Type: numpy array, Shape: {shape}"
    else:
        repr_str, classname = get_truncated_repr(value)
        return f"{repr_str} Type: {classname}"


def get_truncated_repr(obj, limit=30):
    classname = obj.__class__.__name__
    repr_str = repr(obj)
    if len(repr_str) > limit:
        repr_str = repr_str[:limit] + "..." + repr_str[-1:]
    return repr_str, classname


def get_functions_in_prompt(nodes: List[Node]):
    prompt = ""
    for node in nodes:
        func = get_obj(node)
        func_header = get_function_header(func)
        prompt += f"""
Header and content summary of a function:
{func_header}"""
        if node.isinstance(CodeSummary):
            summary = CodeSummary.get_summary(node)
            prompt += f"""    # {summary}
"""
    return prompt


@standard_multi_attempts
def call_function_node(func_nodes: List[Node], var_table: VariableTable,
                       requirement: str):
    prompt = f"""You are required to directly output Python codes to meet the following requirement:
{requirement}
"""
    if len(func_nodes) != 0:
        prompt += f"""
Here are the functions in the scope that you can call to meet the requirement:
"""
        prompt += get_functions_in_prompt(func_nodes)

    prompt += f"""
You are required to output Python code in the following format. You have to write the documentation of the return values. Your code must be executable.
def answer():
    ... (Your code here)
    return return_value_1, return_value_2, ...
    # return_value_1: documentation of the return value
    # return_value_2: documentation of the return value
    # ...
    
"""

    if not var_table.is_empty():
        prompt += f"""
You can use the following variables that is available in the current scope.
Variables:
{var_table.get_prompt()}
"""
    prompt += f"""Requirement of output: 
You are not allowed to modify the variables expect in the line of function call.
You should not use any variable that is not in the current scope.
You should not use import statement.
Start your answer with "def answer()"
"""
    chat = Chat(prompt,
                "You are a code generator who only outputs Python code. You should only output Python code.")
    code_raw = chat.complete_chat_expensive()
    print(chat)

    code_exec = process_and_run_code(code_raw, func_nodes, var_table)

    return code_exec


def process_and_run_code(code_raw, func_nodes, var_table) -> str:
    if "```python" in code_raw:
        code_raw = code_raw.split("```python")[1]
        code_raw = code_raw.split("```")[0]
    new_vars = {}
    code_lines = code_raw.split("\n")
    for i, line in enumerate(code_lines):
        if line.strip().startswith("return"):
            for j in range(i + 1, len(code_lines)):
                line = code_lines[j].strip()
                if line.startswith("#"):
                    line = line[1:].strip()
                    if ":" not in line:
                        continue
                    first = line.index(":")
                    name = line[:first]
                    docs = line[first + 1:]
                    name = name.strip()
                    docs = docs.strip()
                    if name != "None":
                        new_vars[name] = docs
                else:
                    break
            break
    interpreter = var_table.get_interpreter()
    for func_node in func_nodes:
        func = get_obj(func_node)
        interpreter.symtable[func.__name__] = func
    code_exec = code_raw
    if len(new_vars) == 0:
        code_exec += "\nanswer()"
    else:
        return_value = ", ".join(new_vars.keys())
        code_exec += f"""
{return_value} = answer()"""
    interpreter(code_exec)
    for name, docs in new_vars.items():
        var_table.add_variable(name, interpreter.symtable[name], docs)
    return code_exec


@example
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
    available_vars = call_function_node([node], variables,
                                        "the water volume should be water_volume, salt volume is 10. name the returned beaker as zijian_water")
    print(available_vars.get_prompt())


if __name__ == '__main__':
    example()
