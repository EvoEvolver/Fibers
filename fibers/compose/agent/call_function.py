from __future__ import annotations
from typing import List

from fibers.compose.agent.var_table import VariableTable
from fibers.helper.utils import standard_multi_attempts
from fibers.tree.node_class.code_node import get_obj, CodeData, get_source

from fibers.model.chat import Chat

from fibers.compose.decorate.code_summary import CodeSummary
from fibers.compose.utils_code.header import get_function_header
from fibers.tree import Node
from fibers.tree.prompt_utils import get_node_list_prompt


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
            prompt += "Function:\n"
            if node.has_attr(CodeSummary):
                summary = CodeSummary.get_summary(node)
                prompt += f"# {summary}\n"
            prompt += f"""{func_header}"""

        elif node_type == "example":
            prompt += f"""
Example of code to refer:
{get_source(node)}"""
    return prompt


@standard_multi_attempts
def call_function_node(context: str, requirement: str, var_table: VariableTable,
                       hidden_var_table: VariableTable = None):
    prompt = f"""You are required to directly output Python codes to meet the following requirement:
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

Requirement of output:
You should only use variable that is in the current scope.
You must not use import statement!

Again, the requirement is:
{requirement}
<requirement end>

Start your answer with "def step():" (don't add arguments!)
"""
    chat = Chat(prompt,
                "You are a code generator who only outputs Python code.")

    print(chat)
    print("generating code...")

    code_raw = chat.complete_chat_expensive()

    print(code_raw)

    code_exec, new_variables = process_and_run_code(code_raw, var_table, hidden_var_table)

    return code_exec, new_variables

@standard_multi_attempts
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
    if len(interpreter.error) > 0:
        raise ValueError(f"Invalid Python code: {interpreter.error}")
    new_variables = VariableTable()
    for name, docs in new_vars.items():
        var_table.add_variable(name, interpreter.symtable[name], docs)
        new_variables.add_variable(name, interpreter.symtable[name], docs)
    return code_exec, new_variables


def get_code_gen_context(code_nodes, var_table, external_module_docs, func_content_map, context: str = ""):
    var_env = var_table.get_prompt()

    if var_env != "":
        var_env = \
f"""There exist some variables you can use.
<variables start>
{var_env}
<variables end>
"""

    function_nodes = [node for node in code_nodes if
                      node.get_attr(CodeData).module_tree_type == "function"]
    func_env = get_node_list_prompt(function_nodes, func_content_map)
    func_env = \
f"""There exist some functions that might be used to implement the instructions.
<functions start>
{func_env}       
<functions end>
"""

    module_env = ""
    if len(external_module_docs) != 0:
        module_env += """\nModules in scope\n"""
        for var_name, mod_doc in external_module_docs.items():
            module_env += f"{var_name}: {mod_doc} \n"
        module_env += "\n"

    code_gen_env = f"""
{context}
{func_env}
{module_env}
{var_env}
"""

    return code_gen_env