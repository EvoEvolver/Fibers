from typing import List, Dict
from fibers.compose.decorate.code_summary import CodeSummary, \
    summarize_code_tree
from fibers.compose.extract.searcher import CodeSearcher
from fibers.compose.agent.call_function import get_codes_in_prompt
from fibers.compose.agent.var_table import VariableTable, get_repr_in_prompt
from fibers.data_loader.module_to_tree import add_module_tree_to_node
from fibers.helper.cache.cache_service import auto_cache, caching
from fibers.helper.utils import RobustParse, standard_multi_attempts
from fibers.model.chat import Chat
from fibers.tree import Tree, Node
from fibers.tree.node import ContentMap
from fibers.tree.node_class import CodeData
from fibers.tree.node_class.code_node import get_obj
from fibers.tree.prompt_utils import get_node_list_prompt


map_to_code_summary = ContentMap(lambda n: CodeSummary.get_summary(n) or n.content)

class InstructionRunner:
    def __init__(self, modules, external_modules=None,
                 variable_table=None):
        self.modules = modules
        self.var_table = variable_table or VariableTable()
        self.var_table_hidden = VariableTable()

        self.external_module_docs: Dict = {}
        self.load_external_modules(external_modules)

        self.module_tree = Tree("Available modules")
        for module in modules:
            add_module_tree_to_node(module, self.module_tree.root)

        summarize_code_tree(self.module_tree)

        self.code_searcher: CodeSearcher = CodeSearcher(self.module_tree.root)


    def load_external_modules(self, external_modules):
        external_modules = external_modules or []
        for module in external_modules:
            if isinstance(module, tuple) or isinstance(module, list):
                module_name = module[0]
                module_obj = module[1]
            else:
                module_name = module.__name__
                module_obj = module
            module_doc = f"{module_obj.__name__} module"
            self.external_module_docs[module_name] = module_doc
            self.var_table_hidden.add_variable(module_name, module_obj, module_doc)

    def run_instruction(self, instruction: str):

        caching.save()

        code_cells = []
        while True:
            code_context = \
                f"""
Here are the code that you have implemented so far:
{"".join(code_cells)}
<code end>
"""
            if len(code_cells) == 0:
                code_context = "You have not implemented any code yet. \n"
            context = \
                f"""
The instruction you are trying to implement is:
{instruction}
<instruction end>
{code_context}
"""

            next_step = get_next_step(context)

            if next_step == "":
                break

            def search_and_run():
                _function_requirement = "The function can be used to implement the following instruction \n" + next_step + "<instruction end>"
                _related_func_nodes = self.code_searcher.search(_function_requirement,
                                                                ["function"])

                _code = self.run_short_instruction(next_step, _related_func_nodes, "".join(code_cells))
                return _code
            code = search_and_run()
            code_cells.append(code)
            print({"".join(code_cells)})


    def run_short_instruction(self, instruction, code_nodes: List[Node], prev_code):

        for node in code_nodes:
            if node.get_attr(CodeData).module_tree_type == "function":
                func = get_obj(node)
                self.var_table_hidden.add_variable(func.__name__, func, "")

        map_to_code_header = ContentMap(lambda n: get_codes_in_prompt([n]))

        prev_code_context = f"""
Here is the code that you have implemented so far:
{prev_code}
<code end>
"""
        if len(prev_code) == 0:
            prev_code_context = ""

        context = get_code_gen_context(code_nodes, self.var_table,
                                       self.external_module_docs, map_to_code_header, context=prev_code_context)

        code = call_function_node(context, instruction, self.var_table,
                                                 self.var_table_hidden)

        return code

def get_code_gen_context(code_nodes, var_table, external_module_docs, func_content_map, context: str = ""):
    var_env = var_table.get_prompt()

    if var_env != "":
        var_env = \
f"""There exist variables that have define in the scope.
<variables start>
{var_env}
<variables end>
"""

    function_nodes = [node for node in code_nodes if
                      node.get_attr(CodeData).module_tree_type == "function"]
    func_env = get_node_list_prompt(function_nodes, func_content_map)
    func_env = \
f"""Some functions that might be used to implement the instructions have been defined in the scope. The function body is omitted and you can directly call them.
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
"""

    return code_gen_env

@auto_cache
def get_next_step(context: str) -> str:
    prompt = f"""
You are trying to implement some instructions.

{context}

You are going to generate one next step for finishing the instruction.
Output your answer by a JSON dict with first key being "analysis" for a string that analyze the situation. Notice that the information above might be irrelevant to the next step. 
Then second key "next_step" being a string for a detailed plan for the next step.
The next step should be a minimal step that can be executed.
You should only use the information above to generate the next step. 
If you think the instruction is already finished, you should output a empty string.
"""
    chat = Chat(prompt, "You are an helpful analyzer for planing who only output JSON")
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    print(chat)
    next_step = res["next_step"]
    return next_step


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
Requirement of code generation:
Your code will be run in the context/scope defined above, using the functions and variables provided.
You should only use variable that is in the current scope. You are encourage to add concise documentation. You are not encourage to define functions in the output.
...

Again, the requirement is:
{requirement}
<requirement end>

Start your answer with "```python"
"""
    chat = Chat(prompt,
                "You are a code generator who only outputs Python code.")

    print(chat)
    print("generating code...")

    code_raw = chat.complete_chat_expensive()

    print(code_raw)

    code_exec = process_and_run_code(code_raw, var_table, hidden_var_table)

    return code_exec


@standard_multi_attempts
def process_and_run_code(code_raw, var_table, hidden_var_table=None):
    if "```python" in code_raw:
        code_raw = code_raw.split("```python")[1]
        code_raw = code_raw.split("```")[0]
    interpreter = var_table.get_interpreter()
    if hidden_var_table is not None:
        hidden_var_table.add_to_interpreter(interpreter)
    old_vars = set(interpreter.symtable.keys())
    code_exec = code_raw
    interpreter(code_exec)
    if len(interpreter.error) > 0:
        raise ValueError(f"Invalid Python code: {interpreter.error}")
    new_vars = set()
    for var_name in interpreter.symtable.keys():
        if var_name not in old_vars:
            var_table.add_variable(var_name, interpreter.symtable[var_name], "")
            new_vars.add(var_name)
    var_value = []
    for var_name in new_vars:
        var_value.append(f"# {var_name}: {get_repr_in_prompt(interpreter.symtable[var_name])}")
    code_exec = code_raw + "\n" + "\n".join(var_value)
    return code_exec