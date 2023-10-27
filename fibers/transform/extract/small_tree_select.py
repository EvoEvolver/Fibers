from typing import List

import yaml

from fibers.helper.cache.cache_service import cached_function
from fibers.model.chat import Chat
from fibers.tree import Tree


def small_tree_select(tree: Tree, criteria_prompt: str) -> Tree:
    tree_with_indices, note_indexed = tree.get_dict_with_indices_for_prompt()
    tree_in_yaml = yaml.dump(tree_with_indices)
    useful_indices = filter_tree_indices(tree_in_yaml, criteria_prompt)
    useful_notes = [note_indexed[i] for i in useful_indices]
    filtered = Tree.from_nodes(useful_notes)
    return filtered


system_message = "You are a helpful processor for NLP problems. Output answer concisely as if you are a computer program."

@cached_function
def filter_tree_indices(tree_yaml, criteria_prompt) -> \
        List[int]:
    prompt = f"You are working on filtering notes in a database according to its content and the path it is stored. The databased is stored in a YAML file, with each note labelled by an index." \
             f"\n{criteria_prompt}"
    chat = Chat(
        user_message=prompt,
        system_message=system_message)
    chat.add_user_message("The database: \n" + tree_yaml)
    chat.add_user_message(
        f"Output the indices of the notes that satisfies the criteria with indices "
        f"separated by comma (output none when none matches): \n"
        f"{criteria_prompt}.")
    res = chat.complete_chat_expensive()
    original_res = res
    if "none" in res or "None" in res:
        return []
    number_start = -1
    for i in range(len(res)):
        if res[i] in "0123456789":
            number_start = i
            break
    if number_start == -1:
        raise ValueError(f"Invalid answer: {res}")
    number_end = len(res)
    for i in range(number_start, len(res)):
        if res[i] not in "0123456789, ":
            number_end = i
            break
    res = res[number_start:number_end]
    try:
        useful_indices = [int(i.strip()) for i in res.split(",")]
    except Exception as e:
        raise ValueError(f"Invalid answer: {res}, {original_res}")

    return useful_indices