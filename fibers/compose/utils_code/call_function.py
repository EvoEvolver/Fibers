from __future__ import annotations
from types import ModuleType
from typing import List, Tuple

import numpy

from fibers.helper.utils import standard_multi_attempts
from fibers.tree.node_class.code_node import get_obj, CodeData, get_source
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
        self._parent_tables = []

    def add_variable(self, name, obj, docs):
        self.variable_objs[name] = obj
        self.variable_docs[name] = docs

    def get_variable(self, name) -> Tuple["object", str]:
        return self.variable_objs[name], self.variable_docs[name]

    def get_prompt(self):
        prompt_dict = {}
        for table in self._parent_tables:
            prompt_dict.update(table.get_local_prompt_dict())
        prompt_dict.update(self.get_local_prompt_dict())
        prompt_list = [f"{prompt}" for prompt in prompt_dict.values()]
        return "\n".join(prompt_list)

    def get_local_prompt(self):
        prompt_dict = self.get_local_prompt_dict()
        prompt_list = [f"{prompt}" for prompt in prompt_dict.values()]
        return "\n".join(prompt_list)

    def get_local_prompt_dict(self):
        prompt_dict = {}
        for name, docs in self.variable_docs.items():
            value = self.variable_objs[name]
            prompt_dict[name] = f"{name}: {docs}. Value: {get_value_in_prompt(value)}"
        return prompt_dict

    def is_empty(self):
        return len(self.get_prompt().strip()) == 0

    def is_local_empty(self):
        return len(self.get_local_prompt().strip()) == 0

    def get_interpreter(self):
        interpreter = Interpreter()
        self.add_to_interpreter(interpreter)
        return interpreter

    def add_to_interpreter(self, interpreter: Interpreter):
        for parent_table in self._parent_tables:
            for name, obj in parent_table.variable_objs.items():
                interpreter.symtable[name] = obj
        for name, obj in self.variable_objs.items():
            interpreter.symtable[name] = obj
        return interpreter

    def push_new_table(self) -> VariableTable:
        new_table = VariableTable()
        new_table._parent_tables = self._parent_tables + [self]
        return new_table

    def pop_table(self) -> VariableTable:
        return self._parent_tables[-1]


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
    elif isinstance(value, ModuleType):
        name = value.__name__.split(".")[-1]
        return f"Module: {name}"
    else:
        repr_str, classname = get_truncated_repr(value)
        return f"{repr_str} Type: {classname}"


def get_truncated_repr(obj, limit=30):
    classname = obj.__class__.__name__
    repr_str = repr(obj)
    if len(repr_str) > limit:
        repr_str = repr_str[:limit] + "..." + repr_str[-1:]
    return repr_str, classname


def get_codes_in_prompt(nodes: List[Node]):
    prompt = ""
    for node in nodes:
        if not node.has_attr(CodeData):
            prompt += f"""Document:
{node.content}
"""
            continue
        node_type = node.get_attr(CodeData).module_tree_type
        if node_type == "function":
            func = get_obj(node)
            func_header = get_function_header(func)
            prompt += f"""
Function:
{func_header}"""
            if node.has_attr(CodeSummary):
                summary = CodeSummary.get_summary(node)
                prompt += f"""# {summary}
"""
        elif node_type == "example":
            prompt += f"""
Example of code to refer:
{get_source(node)}"""
    return prompt


@standard_multi_attempts
def call_function_node(context: str, requirement: str, var_table: VariableTable,
                       hidden_var_table: VariableTable = None):
    prompt = f"""You are required to directly output Python codes to meet the following requirement:
<requirement>
{requirement}
<requirement end>
"""
    if len(context) != 0:
        prompt += f"""
{context}
"""

    prompt += f"""
You are required to output Python code in the following format. You have to write the documentation of the return values. Your code must be executable. Do not put tuple in return values.
def step():
    ... (Your code here)
    return return_value_1, return_value_2, ...
    # return_value_1: documentation of the return value
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
The return values will overwrite the variables in the scope. And you should only return the required variables.
Again, the requirement is:
{requirement}

Start your answer with "def step():" (don't add arguments!)
"""
    chat = Chat(prompt,
                "You are a code generator who only outputs Python code.")
    code_raw = chat.complete_chat_expensive()
    print("Generating code...")
    print(chat)

    code_exec, new_variables = process_and_run_code(code_raw, var_table, hidden_var_table)

    return code_exec, new_variables


def process_and_run_code(code_raw, var_table, hidden_var_table=None):
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
    if hidden_var_table is not None:
        hidden_var_table.add_to_interpreter(interpreter)
    code_exec = code_raw
    if len(new_vars) == 0:
        code_exec += "\nstep()"
    else:
        return_value = ", ".join(new_vars.keys())
        code_exec += f"""
{return_value} = step()"""
    interpreter(code_exec)
    new_variables = VariableTable()
    for name, docs in new_vars.items():
        var_table.add_variable(name, interpreter.symtable[name], docs)
        new_variables.add_variable(name, interpreter.symtable[name], docs)
    return code_exec, new_variables


