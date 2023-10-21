import json

from fibers.helper.cache.cache_service import cached_function
from fibers.model.chat import Chat
from fibers.tree import Tree


@cached_function
def _small_tree_to_paragraph_impl(dict_for_prompt: str, writing_instruction: str):
    chat = Chat(
        system_message="You are a excellent writer who can transform JSON to a coherent paragraph so human can read it.")
    chat.add_user_message(
        "Please transform the following JSON generated from a knowledge database to a paragraph that can be read by human."
        "\n JSON: \n" + dict_for_prompt +
        f""" 
You should focus more on presenting the `content` of the JSON than the keys.
{writing_instruction}
Start your answer with `Paragraph:`
""")
    res = chat.complete_chat()
    return res

def small_tree_to_paragraph(tree: Tree, writing_instruction: str):
    dict_for_prompt = tree.get_dict_for_prompt()
    dict_for_prompt = json.dumps(dict_for_prompt, indent=1)
    res = _small_tree_to_paragraph_impl(dict_for_prompt, writing_instruction)
    return res