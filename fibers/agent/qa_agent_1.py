from fibers import debug
from fibers.agent import Agent
from fibers.helper.utils import multi_attempts, RobustParse
from fibers.indexing.indexing import Indexing
from fibers.indexing.key_phrase import KeyPhraseIndexing
from fibers.model.chat import Chat
from fibers.transform.extract.small_tree_select import small_tree_select
from fibers.tree import Tree
from fibers.tree.tree import new_tree_from_node_subset


class QuestionAnswerer(Agent):
    def __init__(self, tree: Tree):
        super().__init__()
        self.tree = tree

    def get_answer(self, question):
        res = single_tree_qa(question, self.tree)
        return res


"""
## Main function for the QA agent
"""


@multi_attempts
def single_tree_qa(question: str, knowledge_tree: Tree):
    """
    :param question: The question
    :param knowledge_tree: The tree to search
    :return: The answer
    """
    indexing = KeyPhraseIndexing(knowledge_tree.all_nodes())
    working_memory = Tree("Working Tree")
    working_memory.root.be("")
    old_plan = None
    exit_flag = False
    while not exit_flag:

        question_prompt = f"""Question:{question}"""

        question_context = ""
        if len(working_memory.children) > 1:
            question_context += "Memory of answer of related question:\n"
            question_context += working_memory.get_path_content_str_for_prompt()
            question_context += "\n"
        else:
            question_context += "Memory: empty.\n"

        with debug.display_chats():
            analysis = analyze_question(question_prompt, question_context)
            plan = give_steps(question_prompt, analysis)

        if "first step" not in plan:
            return plan["answer"]
        first_step = plan["first step"]
        if first_step.startswith("Ask: "):
            old_plan = plan
            sub_question = first_step[len("Ask: "):]
            with debug.display_chats():
                ans = answer(sub_question, knowledge_tree, indexing)
            if "answer" in ans:
                working_memory.root.s(sub_question).be(ans["answer"])
            else:
                working_memory.root.s(sub_question).be(
                    "You failed to find the answer of the question.")
        else:
            continue

    return None


"""
## Analyze and planning
"""

system_prompt_json = "You are world-class analyzer for planning a question answering problem. You must output in JSON format."


def analyze_question(question_prompt: str, question_context: str):
    chat = Chat(system_message=system_prompt_json)

    chat.add_user_message(question_prompt + "\n" + question_context)

    prompt_analysis = f"""
You should consider the memory listed above and analyze how the question can be simplified by the memory.
If the question cannot be simplified by the memory, you should analyze how to decompose the question into two simpler questions for searching. Your analysis should be brief.
Start your analysis with `Analysis:`.
"""

    chat.add_user_message(prompt_analysis)

    analysis = chat.complete_chat()

    start = analysis.find(":")
    analysis = analysis[start + 1:].strip()

    return analysis


@multi_attempts
def give_steps(question_prompt: str, analysis: str):
    chat = Chat(system_message=system_prompt_json)

    question_prompt += f"\n\nAnalysis:\n{analysis}"
    chat.add_user_message(question_prompt)

    prompt_steps = """Based on the analysis, you have two options:

    1. If the analysis think an answer can be generated directly, give a JSON string with the key `answer` whose value summarizes the answer.
    2. Else, give a three-step plan for answering the question by a JSON string with keys being`first step`, `second step`, `third step`. Each of your step must start with `Ask:` followed by a question with What, Why, How, etc.
    """

    chat.add_user_message(prompt_steps)

    res = chat.complete_chat()
    res = RobustParse.dict(res)

    return res


"""
## Search
"""


def imagine_answer(query: str, n_fragments=3):
    system_prompt = "You are part of a information searching system."
    prompt = f"""Give fragments of phrases that can be part of the answer to the query of search. 
    For example:
    "What is the capital of France?" -> "The capital of France is"
    "Importance of drink water" -> "Drinking water is important because"
    "How to make a cake" -> "is needed for making a cake"

    Give no more than {n_fragments} fragments in a JSON string with the key `fragments`.
    """
    chat = Chat(user_message=prompt, system_message=system_prompt)
    chat.add_user_message("Question:\n" + query)
    res = chat.complete_chat()
    res = RobustParse.dict(res)
    return res


def search(query: str, tree: Tree, indexing: Indexing):
    imagined_answer = imagine_answer(query)["fragments"]
    selected_nodes = indexing.get_top_k_nodes(imagined_answer, k=10)
    sub_tree = new_tree_from_node_subset(selected_nodes)
    sub_tree = small_tree_select(sub_tree,
                                    "The note answers the search query:" + query)
    return sub_tree


@multi_attempts
def answer(question: str, tree: Tree, indexing: Indexing):
    sub_tree = search(question, tree, indexing)
    prompt = f"""Here is some items obtained from a knowledge base. The context of the items are implied by their path.
{sub_tree.get_path_content_str_for_prompt()}"""
    chat = Chat(user_message=prompt)
    chat.add_user_message(f"""Please analyze and give an answer to the question: 
{question}

If the question can be more or less answered by the items, give a JSON string with the key `analysis` and `answer`.
If the items is irrelevant to the question, give a JSON string with the a single key `analysis`.
""")
    res = chat.complete_chat_expensive()
    res = RobustParse.dict(res)
    return res
