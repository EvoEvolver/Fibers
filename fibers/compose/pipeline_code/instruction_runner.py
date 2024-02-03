import html
from typing import List


from fibers.compose.decorate.code_summary import CodeSummarizedNodeClass, \
    summarize_code_tree
from fibers.compose.extract.code_searcher import make_code_searcher
from fibers.compose.utils_code.call_function import VariableTable, call_function_node
from fibers.data_loader.module_to_tree import add_module_tree_to_node
from fibers.helper.cache.cache_service import auto_cache
from fibers.helper.utils import RobustParse
from fibers.model.chat import Chat
from fibers.tree import Tree, Node
from fibers.tree.node import ContentMap
from fibers.tree.node_class import NodeClass
from fibers.tree.prompt_utils import get_node_list_prompt


class InstRunInfo(NodeClass):
    init_by = "obj"
    def __init__(self):
        self.decomposable = None
        self.executed = False
        self.code = None
        self.var_table_at_run = None
        self.report_of_old_siblings = None
        self.report_of_self = None

    @classmethod
    def render(cls, node: Node, rendered):
        obj = node.class_data[InstRunInfo]
        content = [f"""
    report_of_old_siblings: {obj.report_of_old_siblings} 
    """]
        if obj.code is not None:
            content.append(f"""<Code code = "{html.escape(obj.code)}" language = "python" />""")
        if obj.var_table_at_run is not None:
            content.append(html.escape(obj.var_table_at_run).replace("\n", "<br/>"))

        rendered.tabs["inst_run"] = "<br/>".join(content)


class InstructionRunner:
    def __init__(self, modules, variable_table=None):
        self.modules = modules
        self.variable_table = variable_table or VariableTable()
        self.tree = Tree("Available modules")
        for module in modules:
            add_module_tree_to_node(module, self.tree.root)

        summarize_code_tree(self.tree)

        content_map = ContentMap(
            lambda n: CodeSummarizedNodeClass.get_summary(n) or n.content)
        self.beam_searcher = make_code_searcher("function", content_map)
        self.map_to_code_summary = content_map

    def run_instruction(self, node: Node, related_functions: List[Node]):
        instruction = node.content
        code = call_function_node(related_functions, self.variable_table, instruction)
        node.add_class(InstRunInfo)
        node.class_data[InstRunInfo].executed = True
        node.class_data[InstRunInfo].code = code
        node.class_data[InstRunInfo].var_table_at_run = self.variable_table.get_prompt()
        node.tree.show_tree_gui_react()
        report = code_to_report(code, instruction)
        node.class_data[InstRunInfo].report_of_self = report

    def search_by_requirement(self, requirement) -> List[Node]:
        return self.beam_searcher(self.tree.root, requirement)

    def get_related_functions(self, requirement):
        function_nodes = self.search_by_requirement(requirement)
        return function_nodes

    def get_environment(self, function_nodes, inst_node: Node):

        progress_env = self.get_progress_of_inst_node(inst_node)

        var_env = self.variable_table.get_prompt()

        func_env = get_node_list_prompt(function_nodes, self.map_to_code_summary)
        env = f"""
Progress so far:        
{progress_env}
        
There exist some functions that might be used to implement the instructions.
<functions start>
{func_env}       
<functions end> 

There exist some variables you can use.
<variables start>
{var_env}
<variables end>
"""
        return env

    def get_progress_of_inst_node(self, inst_node):
        children_list = list(inst_node.children().values())
        if len(children_list) == 0:
            sibling_summary = ""
        else:
            youngest_sibling_info = children_list[-1].class_data[InstRunInfo]
            sibling_summary = merge_reports(youngest_sibling_info.report_of_old_siblings,
                                            youngest_sibling_info.report_of_self)
        if len(sibling_summary) == 0:
            progress_env = "Nothing has been done before."
        else:
            progress_env = sibling_summary
        return progress_env

    def grow_instruction_tree(self, inst_node: Node):

        if inst_node.has_child():
            for child in inst_node.children().values():
                self.grow_instruction_tree(child)
            return

        if inst_node.is_empty():
            return

        related_func_nodes = self.get_related_functions(
            "The function can be used to implement the following instructions \n <instruction>" + inst_node.content + "</instruction>")


        word_count = len(inst_node.content.split(" "))
        if word_count < 40:
            self.run_instruction(inst_node, related_func_nodes)
            return


        while True:
            env = self.get_environment(related_func_nodes, inst_node)
            next_step = get_next_step(inst_node.content, env)
            if next_step == "":
                parent = inst_node.parent()
                parent.class_data[InstRunInfo].report_of_old_siblings = self.get_progress_of_inst_node(parent)
                return
            progress_so_far = self.get_progress_of_inst_node(inst_node)
            children_list = list(inst_node.children().values())
            new_child = inst_node.new_child("Step " + str(len(children_list) + 1)).be(next_step)
            new_child.class_data[InstRunInfo] = InstRunInfo()
            new_child.class_data[InstRunInfo].report_of_old_siblings = progress_so_far
            self.grow_instruction_tree(new_child)


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
Output your answer by a JSON dict with first key "next step" being the content of the next step.
How to stop:
If the instruction is already finished and no more step is needed, set the value of "next step" to be a empty string.
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    print(chat)
    next_step = res["next step"]
    return next_step


def code_to_report(code, instruction):
    prompt = f"""
You are trying to report your progress on implementing some instructions.
You are trying to follow this instruction:
{instruction}
This is the code you have written:
{code}

You are trying to summarize the progress that instruction is implemented by the code.
Start your answer with "Summary: ".
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat()
    res = res[len("Summary: "):]
    return res

def merge_reports(report_of_old_sibling, new_report):
    prompt = f"""
You are trying to report your progress on implementing some instructions.
This is what has been done before:
{report_of_old_sibling}
This is what you have done now:
{new_report}

Update the old report with the new report and summarize the progress.
The summary should be no more than 100 words. 
Start your answer with "Summary: ".
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat()
    res = res[len("Summary: "):]
    return res


@auto_cache
def try_decompose(inst: str, environment=""):
    prompt = f"""
You are trying to generate codes based on some instructions.

The instruction/description is as follows:
<instruction start>
{inst}
<instruction end>

{environment}

You are trying to decompose the following instruction. It is decomposable if it contains multiple steps explicitly.
Output your answer by a JSON dict with first key "type" being "directly implementable" or "decomposable".
If it is decomposable, the second key should be "steps" and value should be a list of strings, each string is a step.
You should output that the instruction is "directly implementable" if it can be implemented by a functions above.
You MUST not decompose the function calling. Just output it is "directly implementable" if it is.
"""
    chat = Chat(prompt, "You are an helpful assistant who help analyze instructions.")
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    print(chat)
    if res["type"] == "decomposable":
        return res["steps"]
    else:
        return None





