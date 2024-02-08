from __future__ import annotations
from typing import List

from fibers.compose.agent.var_table import VariableTable
from fibers.helper.utils import standard_multi_attempts
from fibers.tree.node_class.code_node import get_obj, CodeData, get_source

from fibers.model.chat import Chat

from fibers.compose.decorate.code_summary import CodeSummary
from fibers.compose.utils_code.header import get_function_header
from fibers.tree import Node


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


