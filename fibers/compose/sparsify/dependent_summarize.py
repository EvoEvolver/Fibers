from typing import List

from fibers.compose.sparsify.shape_optimize import make_all_content_on_leaf, \
    combine_single_child
from fibers.tree.node_attr import Attr
from moduler.decorator import example
from tqdm import tqdm

from fibers.data_loader.bad_text_node_class import has_bad_reason
from fibers.data_loader.html_to_tree import html_to_tree
from fibers.helper.cache.cache_service import caching, auto_cache
from fibers.helper.utils import parallel_map, RobustParse
from fibers.model.chat import Chat
from fibers.testing.testing_nl_dataset.loader import extract_dataset
from fibers.tree import Tree, Node
from fibers.tree.node_class import NodeClass
from fibers.tree.prompt_utils import get_node_list_prompt


class Chunked(Attr):
    pass

class LayeredSummary(Attr):
    def __init__(self, node: Node):
        super().__init__(node)
        self.layered_summary = None
        self.children_dict = None




@example
def example():
    #tree = load_sample_tree("Feyerabend.md")
    data = extract_dataset("QuALITY.v1.0.1.dev", 1)
    tree = html_to_tree(data["article"], to_markdown=False)
    make_all_content_on_leaf(tree)
    moving_window_decompose(tree.root, window_size=150, overlap_size=20)
    combine_single_child(tree.root)
    group_size = 3
    summary_limit = 200
    for node in list(tree.root.iter_subtree_with_bfs()):
        if node == tree.root:
            continue
        if not node.has_attr(Chunked):
            LayeredSummary.get(node).layered_summary=[[]]
            LayeredSummary.get(node).children_dict={}
        else:
            up_context_on_tree = find_up_context_on_tree(node, group_size=group_size)
            dependent_summarize_node(node, up_context_on_tree, group_size=group_size, summary_limit=summary_limit)
            res_layered_summary = LayeredSummary.get(node).layered_summary
            top_summary = res_layered_summary[-1][0]
            make_layer_summary_for_ancestor(node, top_summary, group_size=group_size, summary_limit=summary_limit)
        caching.save()

    for node in list(tree.root.iter_subtree_with_bfs()):
        if node == tree.root:
            continue
        if node.has_attr(LayeredSummary):
            children_dict = LayeredSummary.get(node).children_dict
            layer_lists = LayeredSummary.get(node).layered_summary
            make_tree_from_layered_summary(node, layer_lists, children_dict)

    #tree.show_tree_gui()

    leaf_nodes = []
    for node in tree.all_nodes():
        if node.has_child():
            continue
        leaf_nodes.append(node)

    question_dict = data["questions"][1]
    qa(question_dict, leaf_nodes)

    #caching.save_used()


def qa(question_dict, leaf_nodes):
    question_prompt = f"""
    {question_dict["question"]} The answer is one of {question_dict["options"]}
    """
    i_golden_answer = question_dict["gold_label"] - 1
    golden_answer = question_dict["options"][i_golden_answer]
    print("Question:", question_prompt)
    print("Options:", question_dict["options"])
    print("Golden answer:", i_golden_answer + 1)
    def find_clue_for_node(node: Node):
        res = find_clue(question_prompt, node)
        return res

    def directly_answer_for_node(node: Node):
        res = directly_answer(question_dict, node)
        return res

    for i, res in parallel_map(find_clue_for_node, leaf_nodes):
        #if res != -1:
        print(i, res)
# Hello 2023-Nov-15
def directly_answer(question_dict, node):
    ancestors = []
    parent = node.parent()
    while parent is not node.tree.root:
        if not parent.is_empty():
            ancestors.append(parent)
        parent = parent.parent()
    ancestors.reverse()
    context = get_node_list_prompt(ancestors)
    question = question_dict["question"]
    options = question_dict["options"]
    option_in_prompt = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
    prompt = f"""
You are trying to answer a question by finding a clue from the content and context.

Context of the content:
{context}

Content:
{node.content}

Question:
{question}

Options:
{option_in_prompt}

Requirements:
You should select one of the options as the answer. If you think the content and context is not enough to answer the question, you should select -1.
Else, select the index of the option that is the answer.
Output a JSON with the first key being `analysis` and the second key being `answer`, which is the number of the option you selected.
"""
    chat = Chat(prompt)
    res = chat.complete_chat()
    res_dict = RobustParse.dict(res)
    return res_dict["answer"]


def find_clue(question, node: Node):
    ancestors = []
    parent = node.parent()
    while parent is not node.tree.root:
        if not parent.is_empty():
            ancestors.append(parent)
        parent = parent.parent()
    ancestors.reverse()
    context = get_node_list_prompt(ancestors)
    prompt = f"""
You are trying to answer a question by finding a clue from the content.

Context of the content:
{context}

Content:
{node.content}

Question:
{question}

Requirements:

The content might be related to the question or not.
You should output a JSON with two fields: `clue` and `related` in order.
`clue` is a string that is a clue to the answer of the question.
`related` is a true/false value indicating whether the content provides clue to the question.
"""
    chat = Chat(prompt)
    res = chat.complete_chat()
    res_dict = RobustParse.dict(res)
    if res_dict["related"]:
        return res_dict["clue"]
    else:
        return None


def make_tree_from_layered_summary(node: Node, layer_lists, children_dict):
    parsed_layer_lists = []
    for i, layer in enumerate(layer_lists):
        parsed_layer = []
        for j, summary in enumerate(layer):
            parsed_layer.append((str((i,j)), summary))
        parsed_layer_lists.append(parsed_layer)

    node_pos_map = {}
    for i_summary, summary in enumerate(parsed_layer_lists[-1]):
        (title, content) = summary
        new_node = node.s(title).be(content)
        node_pos_map[(len(parsed_layer_lists) - 1, i_summary)] = new_node

    for i_layer in reversed(range(2, len(parsed_layer_lists))):
        layer = parsed_layer_lists[i_layer]
        for i_summary in range(len(layer)):
            position = (i_layer, i_summary)
            parent_node = node_pos_map[position]
            for child_pos in children_dict[position]:
                (title, content) = parsed_layer_lists[child_pos[0]][child_pos[1]]
                child_node = parent_node.s(title).be(content)
                node_pos_map[child_pos] = child_node

def moving_window_decompose_impl(content, window_size, overlap_size):
    if len(content) <= window_size:
        return [content]

    split_contents = content.split(" ")
    contents_by_window = []

    for i in range(0, len(split_contents), window_size - overlap_size):
        chunk_end = i + window_size
        chunk_start = i
        if chunk_end > len(split_contents):
            chunk_end = len(split_contents)
            chunk_start = chunk_end - window_size
        chunk = " ".join(split_contents[chunk_start:chunk_end]).strip()
        if len(chunk) > 0:
            contents_by_window.append(chunk)
        if chunk_end == len(split_contents):
            break

    return contents_by_window

def make_layer_summary_for_ancestor(node: Node, new_summary, group_size=3, summary_limit=50):
    parent = node.parent()
    if parent is node.tree.root:
        return
    parent_layered_summary = LayeredSummary.get(parent).layered_summary
    parent_layered_summary[0].append(new_summary)

    if len(parent_layered_summary[0]) % group_size == 0:
        children_dict = LayeredSummary.get(parent).children_dict
        up_context_on_tree = find_up_context_on_tree(parent, group_size=group_size)
        build_layer_list(group_size, parent_layered_summary, up_context_on_tree,
                         children_dict, summary_limit=summary_limit)
    elif len(parent_layered_summary[0]) == len(parent.children()):
        children_dict = LayeredSummary.get(parent).children_dict
        up_context_on_tree = find_up_context_on_tree(parent, group_size=group_size)
        process_remaining_contents(group_size, parent_layered_summary, up_context_on_tree,
                                   children_dict, summary_limit=summary_limit)
        top_summary = parent_layered_summary[-1][0]
        make_layer_summary_for_ancestor(parent, top_summary, group_size=group_size, summary_limit=summary_limit)


def moving_window_decompose(root: Node, window_size=50, overlap_size=10):
    for node in list(root.iter_subtree_with_dfs()):
        if not node.has_child():
            continue
        children_chunks = []
        overlapped_children = []
        has_chunked_children = False
        for child in node.children().values():
            if has_bad_reason(child, "overlap_to_sibling"):
                overlapped_children.append(child)
                chunks = moving_window_decompose_impl(child.content, window_size, overlap_size)
                children_chunks.extend(chunks)
            else:
                if len(overlapped_children) >= 1:
                    Chunked.get(overlapped_children[0]).chunks = children_chunks
                    overlapped_children[0].set_content("")
                    has_chunked_children = True
                    for child in overlapped_children[1:]:
                        child.remove_self()
                children_chunks = []
                overlapped_children = []

        if len(overlapped_children) >= 1:
            Chunked.get(overlapped_children[0]).chunks = children_chunks
            overlapped_children[0].set_content("")
            has_chunked_children = True
            for child in overlapped_children[1:]:
                child.remove_self()

        if has_chunked_children:
            LayeredSummary.get(node).layered_summary= [[]]


def dependent_summarize_node(node: Node, up_context_on_tree: List[str], group_size=3, summary_limit=50):
    assert node.has_attr(Chunked)
    chunks = Chunked.get(node).chunks
    layer_lists, children_dict = dependent_summarize_impl(chunks, up_context_on_tree, group_size, summary_limit)
    LayeredSummary.get(node).layered_summary=layer_lists
    LayeredSummary.get(node).children_dict=children_dict
    #tree = get_tree_of_layer_lists(layer_lists, children_dict)
    #tree.show_tree_gui()
    caching.save()

def dependent_summarize_impl(chunks: List[str], up_context_on_tree: List[str], group_size=3, summary_limit=50):
    layer_lists = [[],]
    children_dict = {}

    for i_chunk in tqdm(range(len(chunks))):
        layer_lists[0].append(chunks[i_chunk])
        build_layer_list(group_size, layer_lists, up_context_on_tree, children_dict,
                         summary_limit)

    process_remaining_contents(group_size, layer_lists, up_context_on_tree, children_dict, summary_limit)
    return layer_lists, children_dict


def build_layer_list(group_size, layer_lists, up_context_on_tree, children_dict,
                     summary_limit):

    def summarize_bottom():
        if len(layer_lists) <= 1:
            layer_lists.append([])
        position = (0, len(layer_lists[0]) - 1)
        up_context = find_up_context_in_layer_lists(layer_lists, (1, len(layer_lists[0]) - 1),
                                                    group_size)
        src_list = position_list_to_src([position], layer_lists)
        summary = summarize_node(src_list, up_context, up_context_on_tree,
                                 summary_limit)
        next_layer = layer_lists[1]
        next_layer.append(summary)
        children_dict[(1, len(next_layer) - 1)] = [position]

    def summarize_higher_summary_for_layer(i_layer):
        layer = layer_lists[i_layer]
        # Only summarize when there is group_size contents
        if len(layer) == 0 or len(layer) % group_size != 0:
            return False

        new_position = (i_layer + 1, len(layer) // group_size - 1)

        if new_position in children_dict:
            return False

        summary_to_be_grouped = [(i_layer, len(layer) - group_size + i_summary) for
                                 i_summary in range(group_size)]

        if len(layer_lists) <= i_layer + 1:
            layer_lists.append([])

        next_layer = layer_lists[i_layer + 1]

        up_context = find_up_context_in_layer_lists(layer_lists, summary_to_be_grouped[0], group_size)

        src_list = position_list_to_src(summary_to_be_grouped, layer_lists)

        summary = summarize_node(src_list, up_context, up_context_on_tree,
                                 summary_limit)

        next_layer.append(summary)
        #next_layer.append(str(summary_to_be_grouped))

        assert new_position == (i_layer + 1, len(next_layer) - 1)

        children_dict[new_position] = summary_to_be_grouped

        return True

    summarize_bottom()

    for i_layer in range(1, len(layer_lists)):
        summarize_higher_summary_for_layer(i_layer)
    caching.save()



def position_list_to_src(position_list, layer_lists):
    src_list = []
    for i_layer, i_summary in position_list:
        src_list.append(layer_lists[i_layer][i_summary])
    return src_list


@auto_cache
def summarize_node(src_list, up_context, up_context_on_tree, summary_limit):
    up_context_src = up_context_on_tree + up_context
    summary_limit = summary_limit
    prompt = f"""
You are trying to break and summarize some content so that they can be better understood.
To provide you a better context, here are some preceding content that form the context of the content to be summarized.
"""
    if len(up_context_src) > 0:
        prompt += f"""
Preceding content:
"""
    for i, content in enumerate(up_context_src):
        prompt += f"{i}. {content}\n"
    if len(src_list) == 1:
        this_src_in_prompt = src_list[0]
    else:
        this_src_in_prompt = "\n".join(
            [f"{i}. {content}" for i, content in enumerate(src_list)])

    prompt += f"""
Content to be summarized:

{this_src_in_prompt}

"""
    prompt += f"""

Requirements:
You should make summary for the content to be summarized.
The content you output should add up to at most {summary_limit} words.
Start your answer with `Summary:` 
"""
    chat = Chat(prompt, "You are an helpful assistant who only output JSON")
    res = chat.complete_chat()
    start = res.find(":")
    res = res[start + 1:].strip()
    return res


def find_up_context_in_layer_lists(layer_lists, position, group_size)->List[str]:
    i_layer, in_layer_position = position
    up_context_pos = []
    i_pos = in_layer_position
    for i_layer in range(i_layer, len(layer_lists)):
        layer = layer_lists[i_layer]
        if i_pos < 0:
            break
        start = i_pos - i_pos % group_size
        end = min(len(layer), i_pos)
        for i_summary in range(start, end):
            up_context_pos.append((i_layer, i_summary))
        i_pos = i_pos // group_size - 1
    up_context = position_list_to_src(up_context_pos, layer_lists)
    return up_context

def find_up_context_on_tree(node: Node, group_size)->List[str]:
    parent = node.parent()
    if parent is node.tree.root:
        return []
    up_context = find_up_context_on_tree(parent, group_size)

    self_index = -1
    for i, (key, child) in enumerate(parent.children().items()):
        if child == node:
            self_index = i
            break
    parent_layered_summary = LayeredSummary.get(parent).layered_summary
    up_context_in_parent = find_up_context_in_layer_lists(parent_layered_summary, (0, self_index), group_size)
    up_context.extend(up_context_in_parent)
    return up_context


def process_remaining_contents(group_size, layer_lists, up_context_on_tree, children_dict, summary_limit):
    no_parent_positions = []
    for i_layer in reversed(range(1, len(layer_lists))):
        layer = layer_lists[i_layer]
        remaining_start = len(layer) - len(layer) % group_size
        for i_summary in range(remaining_start, len(layer)):
            no_parent_positions.append((i_layer, i_summary))

    while len(no_parent_positions) > 1:
        last_group = no_parent_positions[-group_size:]
        up_context = find_up_context_in_layer_lists(layer_lists, last_group[0], group_size)
        last_group_src = position_list_to_src(last_group, layer_lists)
        summary = summarize_node(last_group_src, up_context, up_context_on_tree, summary_limit)
        this_layer, this_position = last_group[0]
        if len(layer_lists) <= this_layer + 1:
            layer_lists.append([])
        next_layer = layer_lists[this_layer + 1]
        next_layer.append(summary)
        new_position = (this_layer + 1, len(next_layer) - 1)
        children_dict[new_position] = last_group
        for i in range(len(last_group)):
            no_parent_positions.pop()
        for i, pos in enumerate(no_parent_positions):
            if (new_position[0] == pos[0] and new_position[1] < pos[1]) or new_position[0] > pos[0] or i == len(no_parent_positions) - 1:
                no_parent_positions.insert(i, new_position)
                break


def get_tree_of_layer_lists(layer_lists, children_dict):
    tree = Tree()
    pos_node_map = {}

    for i_summary, summary in enumerate(layer_lists[-1]):
        new_node = tree.root.s(str(i_summary)).be(summary)
        pos_node_map[(len(layer_lists) - 1, i_summary)] = new_node

    for i_layer in reversed(range(1, len(layer_lists))):
        layer = layer_lists[i_layer]
        for i_summary, summary in enumerate(layer):
            position = (i_layer, i_summary)
            parent_node = pos_node_map[position]
            parent_node.be(summary)
            children_pos = children_dict[position]
            for pos in children_pos:
                new_node = parent_node.s(str(pos))
                pos_node_map[pos] = new_node

    return tree


if __name__ == '__main__':
    example()
