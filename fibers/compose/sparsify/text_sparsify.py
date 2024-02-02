from tqdm import tqdm

from fibers.compose.decorate.text_summary import TextSummaryNode
from fibers.compose.decorate.tree_map import node_map_with_dependency
from fibers.data_loader.bad_text_node_class import has_bad_reason, remove_bad_reason, \
    BadTextNodeClass, add_bad_reason
from fibers.helper.cache.cache_service import cached_function, caching, auto_cache
from fibers.helper.utils import parallel_map, RobustParse
from fibers.model.chat import Chat
from fibers.tree import Tree, Node
from bs4 import BeautifulSoup

from fibers.tree.node import ContentMap
from fibers.tree.prompt_utils import get_node_list_prompt

"""
# Decompose long contents
"""


def count_words(content: str):
    split = content.split(" ")
    # filter out empty strings
    split = [s for s in split if len(s.strip()) > 0]
    return len(split)


@auto_cache
def decompose_content(content: str):
    prompt = f"""
Insert HTML headers to the following part of an article to decompose it into sections of about 100 words.
Each title in the header should summarize the content of the section.
You should output in the format of HTML with header tags being <h1>.

Article part:
{content}
"""
    chat = Chat(prompt, "You are an helpful assistant who only output in HTML format.")
    res = chat.complete_chat()
    soup = BeautifulSoup(res, "html.parser")
    # segment by headers
    segments = []
    segment_title = ""
    segment_contents = []
    for child in soup.children:
        if child.name in ["h1", "h2", "h3"]:
            if len(segment_contents) > 0:
                segments.append(
                    {"title": segment_title, "content": "".join(segment_contents)})
            segment_title = child.text
            segment_contents = []
        else:
            segment_contents.append(str(child))
    if len(segment_contents) > 0:
        segments.append({"title": segment_title, "content": "".join(segment_contents)})

    return segments


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
        for i, res in parallel_map(decompose_content, big_fat_nodes):
            node = big_fat_nodes[i]
            node.reset_title("to_delete")
            new_node = node
            for j, subsection in enumerate(res):
                new_node = new_node.new_sibling_after(subsection["title"])
                new_node.be(subsection["content"])
                if j == 0 or j == len(res) - 1:
                    add_bad_reason(new_node, "overlap_to_sibling")
            node.remove_self()

"""
# Merge related siblings
"""

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
    node_map = {}
    i = 0
    while i < len(children_list) - 1:
        child = children_list[i]
        next_child = children_list[i + 1]
        if not (has_bad_reason(child, "overlap_to_sibling") and
                has_bad_reason(next_child, "overlap_to_sibling")):
            if child.isinstance(BadTextNodeClass):
                remove_bad_reason(child, "overlap_to_sibling")
            i += 1
            continue

        node_1 = get_right_most_descendant(child)
        content_1 = node_1.content

        node_2 = get_left_most_descendant(next_child)
        content_2 = node_2.content

        relation = sibling_relation(content_1, content_2)

        if relation == "parallel":
            remove_bad_reason(child, "overlap_to_sibling")
            i += 1
        elif relation == "subsequent":
            if node_1 in nodes_to_remove:
                node_to_add = node_map[node_1]
            else:
                node_to_add = node_1
            node_to_add.content += "\n" + node_2.content
            node_map[node_2] = node_to_add
            nodes_to_remove.append(node_2)
            children_list = list(root.children().values())
            i -= 1
            i += 2
    if len(children_list) == 0:
        if root.content == "":
            nodes_to_remove.append(root)
        return nodes_to_remove
    if has_bad_reason(children_list[-1], "overlap_to_sibling"):
        if len(children_list) == 1:
            remove_bad_reason(children_list[0], "overlap_to_sibling")
        elif len(children_list) > 1:
            if not (has_bad_reason(children_list[-1], "overlap_to_sibling") and
                    has_bad_reason(children_list[-2], "overlap_to_sibling")):
                remove_bad_reason(children_list[-1], "overlap_to_sibling")
    return nodes_to_remove


def merge_overlapping_siblings_once(tree: Tree) -> bool:
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


"""
# Group related siblings
"""

def reduce_max_children_number(root: Node, max_children_number=5):
    while True:
        dense_nodes = []
        for node in root.iter_subtree_with_dfs():
            if len(node.children()) > max_children_number:
                has_dense_children = False
                for child in node.children().values():
                    if len(child.children()) > max_children_number:
                        has_dense_children = True
                        break
                if not has_dense_children:
                    dense_nodes.append(node)
        if len(dense_nodes) == 0:
            break
        parallel_map(group_children, dense_nodes)
        # buggy
        return



def group_children(node: Node):
    content_map = ContentMap(lambda node: TextSummaryNode.get_attr(node, "text_summary"))
    children_prompt = get_node_list_prompt(list(node.children().values()), content_map)
    prompt = f"""
You are trying to group the following sub-sections into larger chapters based on their content for reducing the number of sub-sections in the article.
The sub-sections and their indices are as follows:
{children_prompt}

Based on the information above, output your grouping in the format of a JSON dict.
The keys of the dict should be the title of the chapter, and the values should be a list of indices of the sub-sections in the chapter.
The titles of the chapters should be a short summary of the content of the sub-sections.
"""
    chat = Chat(prompt, "You are an helpful assistant who only output in JSON format.")
    res = chat.complete_chat()
    print(chat)
    res = RobustParse.dict(res)

    for key, value in res.items():
        group_node = node.new_child(key)
        children = list(node.children().values())
        for i in value:
            if i >= len(children):
                break
            child = children[i]
            old_path = list(child.path())
            new_path = list(group_node.path()) + [old_path[-1]]
            child.reset_path(new_path)



if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree
    from fibers.compose.pipeline_text.tree_preprocess import preprocess_text_tree

    tree = load_sample_tree("Feyerabend.md")
    preprocess_text_tree(tree)
    caching.save_used()
    tree.show_tree_gui_react()
