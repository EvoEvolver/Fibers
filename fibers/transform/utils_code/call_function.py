from typing import Callable

import numpy

from fibers.helper.utils import standard_multi_attempts
from fibers.tree.node_class.code_node import get_obj
from moduler.decorator import example

from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.model.chat import Chat

from fibers.transform.decorate.code_summary import CodeSummarizedNodeClass, \
    summarize_code_tree
from fibers.transform.utils_code.header import get_function_header
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
            res += get_value_in_prompt(value[0]) + ", " + get_value_in_prompt(value[1]) + ", ..."
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

@standard_multi_attempts
def call_function_node(node: Node, var_table: VariableTable, requirement: str):
    func = get_obj(node)
    func_header = None
    try:
        func_header = get_function_header(func)
    except:
        print(func)

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
    "variable_names": <list of names of the variable for storing the result. it contains one element when the return value is single>,
    "variable_docs": <list of documentation of the variable for better understanding of others. should match with variable_names>,
    "args": [arg1, arg2, ...] (without quotes if you refer to variables),
    "kwargs": {"kwarg1": kwarg1, ...}
}"""
    prompt += """
Please refer to the function header for a correct format of the arguments.
"""
    if not var_table.is_empty():
        prompt += f"""
You can use the following variables for the arguments. 
Variables:
{var_table.get_prompt()}

Important: When you use them in args or kwargs, you should use the variable name directly, without quotes!
"""
    chat = Chat(prompt, "You are a helpful assistant who call Python functions. You should only output Python objects.")
    res = chat.complete_chat_expensive()
    print(chat)
    exec_function(func, res, var_table)
    return var_table

def exec_function(func: Callable, caller_dict_str: str, var_table: VariableTable):
    interpreter = var_table.get_interpreter()
    caller_dict = interpreter(caller_dict_str)
    args = caller_dict["args"]
    kwargs = caller_dict["kwargs"]
    return_value = func(*args, **kwargs)
    variable_names = caller_dict["variable_names"]
    variable_docs = caller_dict["variable_docs"]
    if len(variable_names) == 0:
        return
    if len(variable_names) == 1:
        return_value = (return_value,)
    if len(variable_names) > 1:
        if not isinstance(return_value, tuple):
            raise ValueError("The return value is not a tuple, but the variable_names has more than one element.")
        if len(variable_names) != len(return_value):
            raise ValueError("The length of variable_names is not equal to the length of the return value.")
    for name, value, docs in zip(variable_names, return_value, variable_docs):
        var_table.add_variable(name, value, docs)

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
    available_vars = call_function_node(node, variables,
                                        "the water volume should be water_volume, salt volume is 10. name the returned beaker as zijian_water")
    print(available_vars.get_prompt())


if __name__ == '__main__':
    example()
