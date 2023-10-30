from tqdm import tqdm

from fibers.helper.cache.cache_service import cached_function, cache_service
from fibers.helper.utils import RobustParse, parallel_map
from fibers.model.chat import Chat
from fibers.tree import Tree, Node


def count_words(content: str):
    split = content.split(" ")
    # filter out empty strings
    split = [s for s in split if len(s.strip()) > 0]
    return len(split)

system_message = "You are a helpful assistant for arranging knowledge. You should output merely JSON."

@cached_function
def decompose_content(content: str):
    prompt = f"""
Decompose the following part of an article into a list of segments, each of which labelled by a title that summaries its content.
You should not add any new information to the content.
You should output in the format of JSON, starting with `[` and ending with `]`. Each of the element in the list should be a JSON object with two fields: `title` and `content`.
You should output with a minimal modification of the original content in the field `content`.
You should use \\" for quotation instead of ".
You should make 2 or 3 segments.
Article part:
{content}
"""
    chat = Chat(prompt, system_message)
    res = chat.complete_chat()
    subsection_list = RobustParse.list(res)
    return subsection_list


@cached_function
def summary_content(content: str, fat_limit):
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


def weight_reduce_brutal(tree: Tree, fat_limit=50):
    while True:
        big_fat_nodes = []
        mid_fat_nodes = []
        for node in tree.iter_with_bfs():
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

        for node in big_fat_nodes:
            node.be("")

        def summarize_to_limit(content_: str):
            return summary_content(content_, fat_limit)

        mid_fat_contents = [node.content for node in mid_fat_nodes]
        for i, summary in parallel_map(summarize_to_limit, mid_fat_contents):
            mid_fat_nodes[i].be(summary)


@cached_function
def sibling_relation(content_1, content_2):
    prompt = f"""
You are trying to figure out the relation between two pieces of content.
There relation can be one of the following:
- `parallel`: the two pieces of content are nearly independent
- `subsequent`: the second piece of content is a continuation of the first piece of content

First content:
{content_1}

Second content:
{content_2}

Start your answer with `Relation:`
"""
    chat = Chat(prompt)
    res = chat.complete_chat()
    start = res.find(":")
    res = res[start + 1:].strip()
    if "parallel" in res:
        return "parallel"
    elif "subsequent" in res:
        return "subsequent"
    else:
        raise ValueError(f"Unknown relation: {res}")




def get_right_most_descendant(node: Node):
    if len(node.children()) == 0:
        return node
    else:
        return get_right_most_descendant(list(node.children().values())[-1])

def get_left_most_descendant(node: Node):
    if len(node.children()) == 0:
        return node
    else:
        return get_left_most_descendant(list(node.children().values())[0])

def merge_children(root: Node):
    children_list = list(root.children().values())
    nodes_to_remove = []
    i = 0
    while i < len(children_list) - 1:
        child = children_list[i]
        next_child = children_list[i + 1]
        if not child.meta.get("overlap_to_sibling", False) or not next_child.meta.get("overlap_to_sibling", False):
            if "overlap_to_sibling" in child.meta:
                del child.meta["overlap_to_sibling"]
            i += 1
            continue

        node_1 = get_right_most_descendant(child)
        content_1 = node_1.content

        node_2 = get_left_most_descendant(next_child)
        content_2 = node_2.content

        relation = sibling_relation(content_1, content_2)

        if relation == "parallel":
            child.meta["overlap_to_sibling"] = False
            i += 1
        elif relation == "subsequent":
            node_1.content += "\n" + node_2.content
            nodes_to_remove.append(node_2)
            children_list = list(root.children().values())
            i -= 1
            i += 2
    if len(children_list) == 0:
        if root.content == "":
            nodes_to_remove.append(root)
        return nodes_to_remove
    if "overlap_to_sibling" in children_list[-1].meta:
        if len(children_list) == 1:
            del children_list[0].meta["overlap_to_sibling"]
        elif len(children_list) > 1:
            if not (children_list[-1].meta["overlap_to_sibling"] and children_list[-2].meta.get("overlap_to_sibling", False)):
                del children_list[-1].meta["overlap_to_sibling"]
    return nodes_to_remove

def merge_overlapping_siblings_once(tree: Tree)->bool:
    nodes_to_remove = []
    nodes = list(tree.iter_with_dfs())
    for node in tqdm(nodes):
        nodes_to_remove += merge_children(node)
    for node in nodes_to_remove:
        node.remove_self()
    return len(nodes_to_remove) > 0

def break_and_merge_siblings(tree: Tree, fat_limit=100, max_iter=10):
    for i in range(max_iter):
        weight_reduce_brutal(tree, fat_limit)
        finished = merge_overlapping_siblings_once(tree)
        if finished:
            break
    weight_reduce_brutal(tree, fat_limit)





if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    break_and_merge_siblings(tree)
    weight_reduce_brutal(tree, 50)
    cache_service.save_cache()
    tree.show_tree_gui()