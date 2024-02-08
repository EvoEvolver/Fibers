import html
from typing import List, Dict

from fibers.compose.decorate.code_summary import CodeSummary, \
    summarize_code_tree
from fibers.compose.extract.searcher import CodeSearcher, DocsSearcher
from fibers.compose.utils_code.call_function import VariableTable, call_function_node, \
    get_codes_in_prompt
from fibers.data_loader.module_to_tree import add_module_tree_to_node
from fibers.helper.cache.cache_service import auto_cache, caching
from fibers.helper.utils import RobustParse, parallel_map
from fibers.model.chat import Chat
from fibers.tree import Tree, Node
from fibers.tree.node import ContentMap
from fibers.tree.node_attr import Attr
from fibers.tree.node_class import CodeData
from fibers.tree.node_class.code_node import get_obj
from fibers.tree.prompt_utils import get_node_list_prompt


class InstRun(Attr):
    def __init__(self, node: Node):
        super().__init__(node)
        self.code = None
        self.var_table_at_run = None
        self.report_of_self = ""


    def render(self, node: Node, rendered):
        content = [f"""
    report_of_self: {html.escape(self.report_of_self)} 
    """]
        if self.code is not None:
            content.append(f"""<Code code = "{html.escape(self.code)}" language = "python" />""")
        if self.var_table_at_run is not None:
            content.append(html.escape(self.var_table_at_run).replace("\n", "<br/>"))

        rendered.tabs["inst_run"] = "<span>"+"<br/>".join(content)+"</span>"


class InstructionRunner:
    def __init__(self, modules, docs_tree=None, external_modules=None, variable_table=None):
        self.modules = modules
        self.var_table = variable_table or VariableTable()
        self.var_table_hidden = VariableTable()

        self.external_modules: Dict = {}
        external_modules = external_modules or []
        for module in external_modules:
            if isinstance(module, tuple) or isinstance(module, list):
                module_name = module[0]
                module_obj = module[1]
            else:
                module_name = module.__name__
                module_obj = module
            module_doc = f"{module_obj.__name__} module"
            self.external_modules[module_name] = module_doc
            self.var_table_hidden.add_variable(module_name, module_obj, module_doc)

        self.module_tree = Tree("Available modules")
        for module in modules:
            add_module_tree_to_node(module, self.module_tree.root)

        summarize_code_tree(self.module_tree)

        self.code_searcher: CodeSearcher = CodeSearcher(self.module_tree.root)

        self.doc_searcher: DocsSearcher = None
        if docs_tree is not None:
            self.doc_searcher: DocsSearcher = DocsSearcher(docs_tree.root)

        self.map_to_code_summary = ContentMap(
            lambda n: CodeSummary.get_summary(n) or n.content)

        self.inst_run_limit = 40

    def run_short_instruction(self, inst_node: Node, code_nodes: List[Node]):
        instruction = NormInst.get(inst_node).get_prompt()
        context = ""
        if len(code_nodes) != 0:
            context += f"""Here are the functions in the scope that you can call to meet the requirement: """
            context += get_codes_in_prompt(code_nodes)
        if len(self.external_modules) != 0:
            context += """\nHere are modules you can directly use without import\n"""
            for var_name, mod_doc in self.external_modules.items():
                context += f"{var_name}: {mod_doc} \n"
            context += "\n"

        self.var_table_hidden = self.var_table_hidden.push_new_table()
        for node in code_nodes:
            if node.get_attr(CodeData).module_tree_type == "function":
                func = get_obj(node)
                self.var_table_hidden.add_variable(func.__name__, func, "")

        code, new_variables = call_function_node(context, instruction, self.var_table, self.var_table_hidden)
        self.var_table_hidden = self.var_table_hidden.pop_table()

        inst_info: InstRun = inst_node.get_attr(InstRun)
        inst_info.code = code
        inst_info.var_table_at_run = self.var_table.get_prompt()
        report = code_to_report(code, instruction, new_variables)
        inst_info.report_of_self = report

        parent_info = inst_node.parent().get_attr(InstRun)
        parent_info.report_of_self = merge_reports(parent_info.report_of_self, report, NormInst.get(inst_node).get_prompt())






    def grow_instruction_tree(self, inst_node: Node):
        if not inst_node.has_attr(NormInst):
            parallel_map(normalize_inst_node, inst_node.iter_subtree_with_dfs())

        caching.save()

        inst_info = InstRun.get(inst_node)

        if inst_node.has_child():
            for child in inst_node.children().values():
                InstRun.get(child).report_of_self = inst_info.report_of_self
                self.grow_instruction_tree(child)
                inst_info.report_of_self = merge_reports(inst_info.report_of_self, child.get_attr(InstRun).report_of_self, NormInst.get(inst_node).get_prompt())
            return

        norm_inst = NormInst.get(inst_node)
        if len(norm_inst.procedure) == 0:
            return

        # The inst_node is not empty
        # The inst_node has no child
        # This two points implies we need to grow the tree

        # Search for related functions
        function_requirement = "The children might be useful to implement the following instructions \n <instruction>" + norm_inst.get_prompt() + "</instruction>"
        related_func_nodes = self.code_searcher.search(function_requirement, ["function", "example"])

        #related_docs_nodes = self.doc_searcher.search(inst_node.content)

        if len(related_func_nodes) == 0:
            pass

        # Decides cases
        # Need sub steps: if the instruction cannot be grounded to codes without referring to the documentations
        # Inst to code: if the instruction can be grounded to codes directly
        # No clue: if the instruction cannot be grounded to either codes or documentations
        # If no clue: use llm to generate or ask human


        word_count = len(" ".join(norm_inst.procedure).split(" "))
        if word_count < self.inst_run_limit:
            self.run_short_instruction(inst_node, related_func_nodes)
            inst_node.tree.show_tree_gui_react()
            return

        # The instruction is long, so we need to decompose it
        self.var_table = self.var_table.push_new_table()
        while True:
            env = self.get_environment(related_func_nodes, inst_node)

            print("generating next step")

            next_steps, exp_result, title = get_next_step(NormInst.get(inst_node).get_procedure_prompt(), env)

            if len(next_steps) > 0:
                new_child = inst_node.new_child(title)
                norm_inst = NormInst(new_child)
                norm_inst.procedure = next_steps
                norm_inst.result = exp_result
                InstRun.get(new_child).report_of_self = ""

                new_child.tree.show_tree_gui_react()

                self.grow_instruction_tree(new_child)
            else:
                # Whenever go up to parent, we try discard some variables
                self.reduce_var_table(inst_node)
                break

    def reduce_var_table(self, inst_node):
        var_names_to_keep = filter_variables(self.var_table, inst_node)
        parent_table = self.var_table.pop_table()
        for var_name in var_names_to_keep:
            try:
                obj, docs = self.var_table.get_variable(var_name)
                parent_table.add_variable(var_name, obj, docs)
            except KeyError:
                pass
        self.var_table = parent_table

    def get_environment(self, code_nodes, inst_node: Node):

        progress_env = InstRun.get(inst_node).report_of_self

        var_env = self.var_table.get_prompt()

        function_nodes = [node for node in code_nodes if
                          node.get_attr(CodeData).module_tree_type == "function"]
        func_env = get_node_list_prompt(function_nodes, self.map_to_code_summary)
        func_env = f"""
There exist some functions that might be used to implement the instructions.
<functions start>
{func_env}       
<functions end> """

        module_env = ""
        if len(self.external_modules) != 0:
            module_env += """\nModules in scope\n"""
            for var_name, mod_doc in self.external_modules.items():
                module_env += f"{var_name}: {mod_doc} \n"
            module_env += "\n"

        env = ""
        if progress_env != "":
            env += f"""
Progress so far:        
{progress_env}
"""
        env += f"""
{func_env}

{module_env}

There exist some variables you can use.
<variables start>
{var_env}
<variables end>
"""
        return env




def filter_variables(var_table, inst_node: Node):
    prompt = f"""
You tried to follow the instruction below and have finished it.
<instruction start>
{NormInst.get(inst_node).get_prompt()}
<instruction end>

Your task now is to pick the variables that can be treated as the output of the instruction.
To do this, you need to think what is the intermediate result of the instruction and what is the final result according to the instruction.
Variables:
<variables start>
{var_table.get_local_prompt()}
<variables end>

Output your answer by a JSON dict with the first key being "analysis", whose value is a string that analyze the situation.
The second key should be "variables" whose value is a list of strings, each string is a variable name to be treated as the output.
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instruction execution.")
    res = chat.complete_chat()
    print(chat)
    res = RobustParse.dict(res)
    return res["variables"]


@auto_cache
def get_next_step(inst: str, environment=""):
    prompt = f"""
You are trying to implement some instructions by calling Python functions.

The instruction/description is as follows:
<instruction start>
{inst}
<instruction end>

{environment}

You are going to generate one step the next step of for finishing the instruction.
Output your answer by a JSON dict with first key being "analysis" for a string that analyze the situation. Notice that the information above might be irrelevant to the next step. 
The second key should be "finished" whose value is a boolean. If only some of the points are finished, you should output false.
Then third key "next_steps" being a list of strings of the plan for next a few steps for others who don't know the context to carry out. The list should contain as few steps as possible.
The forth key "result" should be a list of description of the expected result of the next steps.
The forth key "title" being a string that summarize the next steps.
"""
    chat = Chat(prompt, "You are an helpful analyzer for planing who only output JSON")
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    print(chat)
    next_steps = res["next_steps"]
    if res["finished"]:
        return [], [], ""
    else:
        return next_steps, res["result"], res["title"]


def code_to_report(code, instruction, new_variables: VariableTable):
    prompt = f"""
You are trying to report your progress on implementing some instructions.
You are trying to follow this instruction:
{instruction}
This is the code you have written:
{code}
"""
    if not new_variables.is_local_empty():
        prompt += f"""
Here is the results you have got:
{new_variables.get_prompt()}
"""
    prompt += """
You are trying to summarize the progress that instruction is implemented by the code.
You do not need to mention the detail of code in the summary.
Start your answer with "Summary: ".
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat()
    res = res[len("Summary: "):]
    return res


def merge_reports(report_of_old_sibling, new_report, instruction):
    report_of_old_sibling = report_of_old_sibling if report_of_old_sibling != "" else "Nothing has been done."
    prompt = f"""
You are trying to report your progress on implementing some instructions.
The instruction is as follows:
<instruction>
{instruction}
<instruction end>
This is what has been done before:
<old report>
{report_of_old_sibling}
<old report end>
This is what you have done now:
<new report>
{new_report}
<new report end>

Update the old report with the new report and summarize the progress.
The summary should be no more than 100 words. 
Also, you need to decide whether the instruction is finished or not.
Output your answer in a JSON dict with the first key being "analysis", whose value is a string that analyzes the situation. 
Then, the section key should be "summary" whose value is a string that summarizes the current progress as a reference for deciding the next step.
"""

    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat()
    res = RobustParse.dict(res)

    return res["summary"]


class NormInst(Attr):
    def __init__(self, node: Node):
        super().__init__(node)
        self.procedure = []
        self.result = []
        self.knowledge = []

    def render(self, node: Node, rendered):
        content = f"""
Procedure: {list_to_prompt(self.procedure)}<br/>
Result: {list_to_prompt(self.result)}<br/>
Knowledge: {list_to_prompt(self.knowledge)}
"""
        rendered.tabs["NormInst"] = content

    def get_procedure_prompt(self):
        return list_to_prompt(self.procedure)

    def get_prompt(self):
        res = ""
        if len(self.procedure) == 0:
            res += "The node is empty"
        else:
            res += self.get_procedure_prompt()
        if len(self.result) != 0:
            res += f"""
Expected result: 
{list_to_prompt(self.result)}"""
        if len(self.knowledge) != 0:
            res += f"""
Knowledge:
{list_to_prompt(self.knowledge)}"""
        return res


def list_to_prompt(l):
    return "\n".join([f"{i+1}. {html.escape(c)}" for i, c in enumerate(l)])


@auto_cache
def normalize_inst_node(node: Node):
    if node.is_empty() or node.has_attr(NormInst):
        return
    prompt = f"""
You are trying to divide the content into 3 parts: 
- procedure to execute
- the final result expected by the description (ignoring intermediate results)
- knowledge for executing the procedures that is hard to include in the procedure part.

You output should be a JSON dict with keys being "procedure", "result" and "knowledge", each of which should be a list of strings. 
You should try your best not lose any information in the content.

The content is:
{node.content}
<end>

Start your answer.
"""
    chat = Chat(system_message="You are a useful assistant who only output JSON")
    chat.add_user_message(prompt)
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    #node.content = list_to_prompt(res["procedure"])
    inst_content = NormInst(node)
    inst_content.procedure = res["procedure"]
    inst_content.result = res["result"]
    inst_content.knowledge = res["knowledge"]
