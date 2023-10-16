from fibers.helper.cache.cache_service import cached_function
from fibers.helper.utils import RobustParse, parallel_map, multi_attempts
from fibers.model.chat import Chat
from fibers.tree import Tree, Node


def bfs_on_tree(tree: Tree):
    stack = []
    stack.append(tree.root)
    while len(stack) > 0:
        curr_node = stack.pop(0)
        yield curr_node
        for child in curr_node.children().values():
            stack.append(child)

def count_words(content: str):
    split = content.split(" ")
    # filter out empty strings
    split = [s for s in split if len(s.strip()) > 0]
    return len(split)

fat_limit = 50
system_message = "You are a helpful assistant for arranging knowledge. You should output merely JSON."
@multi_attempts
@cached_function
def decompose_content(content: str):
    prompt = f"""
Decompose the following part of an article into a list of segments, each of which labelled by a title that summaries its content.
You should not add any new information to the content.
You should output in the format of JSON, starting with `[` and ending with `]`. Each of the element in the list should be a JSON object with two fields: `title` and `content`.
You should output with a minimal modification of the original content in the field `content`.
Article part:
{content}
"""
    chat = Chat(prompt, system_message)
    res = chat.complete_chat()
    subsection_list = RobustParse.list(res)
    return subsection_list

@multi_attempts
@cached_function
def summary_content(content: str):
    prompt = f"""
Summarize the following part of an article into a paragraph not longer than {fat_limit - 10} words.
You should not add any new information to the content.
You can discard some information to meet the word limit.
You should output in the format of JSON, with a single field `summary`.
Article part:
{content}
"""
    chat = Chat(prompt, system_message)
    res = chat.complete_chat()
    summary = RobustParse.dict(res)["summary"]
    if count_words(summary) > fat_limit:
        raise ValueError(f"Summary too long ({count_words(summary)} words): {summary}")
    return summary


def weight_reduce_brutal(tree: Tree):
    while True:
        big_fat_nodes = []
        mid_fat_nodes = []
        for node in bfs_on_tree(tree):
            if count_words(node.content) > fat_limit * 1.5:
                big_fat_nodes.append(node)
            elif count_words(node.content) > fat_limit:
                mid_fat_nodes.append(node)
        if len(big_fat_nodes) == 0:
            break
        print(f"Fat nodes: {len(big_fat_nodes)}/{len(tree.all_nodes())}")
        big_fat_contents = [node.content for node in big_fat_nodes]

        for i, subsections in parallel_map(decompose_content, big_fat_contents):
            for subsection in subsections:
                title = subsection["title"]
                content = subsection["content"]
                big_fat_nodes[i].s(title).be(content)

        for i, summary in parallel_map(summary_content, big_fat_contents):
            big_fat_nodes[i].be(summary)

        mid_fat_contents = [node.content for node in mid_fat_nodes]
        for i, summary in parallel_map(summary_content, mid_fat_contents):
            mid_fat_nodes[i].be(summary)


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    weight_reduce_brutal(tree)
    tree.show_tree_gui()