import html
from typing import List


from fibers.compose.decorate.code_summary import CodeSummary, \
    summarize_code_tree
from fibers.compose.extract.searcher import CodeSearcher, DocsSearcher
from fibers.compose.utils_code.call_function import VariableTable, call_function_node, \
    get_codes_in_prompt
from fibers.data_loader.module_to_tree import add_module_tree_to_node
from fibers.helper.cache.cache_service import auto_cache
from fibers.helper.utils import RobustParse
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
        self.decomposable = None
        self.code = None
        self.var_table_at_run = None
        self.report_of_old_siblings = None
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

        self.external_modules = external_modules or []
        for module in self.external_modules:
            self.var_table_hidden.add_variable(module.__name__, module, f"The {module.__name__} module")

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
        instruction = inst_node.content
        context = ""
        if len(code_nodes) != 0:
            context += f"""Here are the functions in the scope that you can call to meet the requirement: """
            context += get_codes_in_prompt(code_nodes)
        if len(self.external_modules) != 0:
            context += """\nHere are modules you can use\n"""
            for mod in self.external_modules:
                context += f"""{mod.__name__}"""
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
        parent_info.report_of_self = merge_reports(parent_info.report_of_self, report, inst_node.content)



        inst_node.tree.show_tree_gui_react()


    def grow_instruction_tree(self, inst_node: Node):
        progress_so_far = None
        if inst_node.parent() is None:
            progress_so_far = self.get_progress_of_inst_node(inst_node.parent())

        inst_info = InstRun.get(inst_node)

        if inst_node.has_child():
            for child in inst_node.children().values():
                InstRun.get(child).report_of_self = inst_info.report_of_self
                self.grow_instruction_tree(child)
                inst_info.report_of_self = merge_reports(inst_info.report_of_self, child.get_attr(InstRun).report_of_self, inst_node.content)
            return

        if inst_node.is_empty():
            return

        # The inst_node is not empty
        # The inst_node has no child
        # This two points implies we need to grow the tree

        # Search for related functions
        function_requirement = "The children might be useful to implement the following instructions \n <instruction>" + inst_node.content + "</instruction>"
        related_func_nodes = self.code_searcher.search(function_requirement, ["function", "example"])

        #related_docs_nodes = self.doc_searcher.search(inst_node.content)

        if len(related_func_nodes) == 0:
            pass

        # Decides cases
        # Need sub steps: if the instruction cannot be grounded to codes without referring to the documentations
        # Inst to code: if the instruction can be grounded to codes directly
        # No clue: if the instruction cannot be grounded to either codes or documentations
        # If no clue: use llm to generate or ask human


        word_count = len(inst_node.content.split(" "))
        if word_count < self.inst_run_limit:
            self.run_short_instruction(inst_node, related_func_nodes)
            return

        # The instruction is long, so we need to decompose it
        self.var_table = self.var_table.push_new_table()
        while True:
            env = self.get_environment(related_func_nodes, inst_node)
            next_step = get_next_step(inst_node.content, env)

            if next_step != "":
                children_list = list(inst_node.children().values())
                new_child = inst_node.new_child("Step " + str(len(children_list) + 1)).be(
                    next_step)
                self.grow_instruction_tree(new_child)

            else:
                inst_node.get_attr(InstRun).report_of_self = self.get_progress_of_inst_node(inst_node)
                # Whenever go up to parent, we try discard some variables
                self.reduce_var_table(inst_node)

                break

    def reduce_var_table(self, inst_node):
        var_names_to_keep = filter_variables(self.var_table, inst_node)
        parent_table = self.var_table.pop_table()
        for var_name in var_names_to_keep:
            obj, docs = self.var_table.get_variable(var_name)
            parent_table.add_variable(var_name, obj, docs)
        self.var_table = parent_table

    def get_environment(self, code_nodes, inst_node: Node):

        progress_env = self.get_progress_of_inst_node(inst_node)

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
            module_list = [f"{module.__name__}" for module in self.external_modules]
            module_env = "Available modules:\n" + "\n".join(module_list)

        env = ""
        if progress_env != "":
            env += f"""
Progress so far:        
{progress_env}
"""
        env = f"""
{func_env}

{module_env}

There exist some variables you can use.
<variables start>
{var_env}
<variables end>
"""
        return env

    def get_progress_of_inst_node(self, inst_node):
        inst_info: InstRun = inst_node.get_attr(InstRun)
        return inst_info.report_of_self




def filter_variables(var_table, inst_node: Node):
    prompt = f"""
You tried to follow the instruction below and have finished it.
<instruction start>
{inst_node.content}
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
You are trying to generate codes based on some instructions.

The instruction/description is as follows:
<instruction start>
{inst}
<instruction end>

{environment}

You are going to generate one step the next step of for finishing the instruction.
Output your answer by a JSON dict with first key being "analysis" for a string that analyze the situation *step-by-step*. Notice that the information above might be irrelevant to the next step. 
The second key should be "finished" whose value is a boolean. If only some of the points are finished, you should output false.
Then third key "next step" being a concise description of the next step for the instruction in *natural language* for passing to someone else to execute.
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat(options={"model": "gpt-4"})
    res = RobustParse.dict(res)
    print(chat)
    next_step = res["next step"]
    if res["finished"]:
        return ""
    else:
        return next_step


def code_to_report(code, instruction, new_variables: VariableTable):
    prompt = f"""
You are trying to report your progress on implementing some instructions.
You are trying to follow this instruction:
{instruction}
This is the code you have written:
{code}
"""
    if not new_variables.is_empty():
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

    print(chat)
    return res["summary"]



