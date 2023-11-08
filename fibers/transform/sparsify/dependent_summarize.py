import math
from typing import List

from moduler.decorator import example

from fibers.helper.cache.cache_service import caching, auto_cache
from fibers.model.chat import Chat
from fibers.tree import Tree


@example
def example():
    chunks = moving_window_decompose("""
Feyerabend therefore returned, still on crutches, to his parents“ apartment house in Vienna’s 15th district. Although he planned to study physics, maths and astronomy, he chose instead to read history and sociology at the University of Vienna’s *Institut für Osterreichische Geschichtsforschung*, thinking that history, unlike physics, is concerned with real life. But he became dissatisfied with history, and returned to theoretical physics. Together with a group of science students, who all regarded themselves as far superior to students of other subjects, Feyerabend invaded philosophy lectures and seminars. Although this was not his first contact with philosophy, it seems to have been the period which cemented his interest. He recalls that in all interventions he took the radical positivist line that science is the basis of knowledge; that it is empirical; and that nonempirical enterprises are either logic or nonsense (p. 68). These views would have been familiar from the climate of Logical Positivism which found its main root in the Vienna Circle, a group of scientifically-minded philosophers who, in the nineteen-twenties and ”thirties sought to deploy the newly-revitalised formal logic of Gottlob Frege and Russell and Whitehead’s *Principia Mathematica* to represent the structure of human knowledge. As we shall see, Feyerabend’s youthful positivist scientism makes quite a contrast with his later conclusions.
In August 1948, at the first meeting of the international summer seminar of the Austrian College Society in Alpbach which he attended, Feyerabend met the philosopher of science Karl Popper, who had already made a name for himself as the Vienna Circle’s “official opposition”. (The Austrian College Society had been founded in 1945 by Austrian resistance fighters, “to provide a forum for the exchange of scholars and ideas and so to prepare the political unification of Europe” (*Science in a Free Society*, p. 109)). In his 1934 book *Logik der Forschung* Popper had elaborated the straightforward and appealing falsificationist view that great science could be characterised as a process in which thinkers put forward bold conjectures and then do their best to improve them by trying to refute them. Instead of trying to develop an inductive logic, Popper argued for the (deductivist) view that scientific method could be characterised in terms of logically valid deductive inferences.
Popper’s own autobiography, unfortunately, tells us nothing about their meeting or their relationship, despite the fact that he was to be the largest single influence (first positive, then negative) on Feyerabend’s work. For those hoping that Feyerabend might use the occasion of his autobiography to settle accounts with his erstwhile philosophical conscience, it is disappointing that the book tells us so little about his acquaintance with Popper. Elsewhere Feyerabend tells us that he
> admired [Popper’s] freedom of manners, his cheek, his disrespectful attitude towards the German philosophers who gave the proceedings weight in more senses than one, his sense of humour… [and] his ability to restate ponderous problems in simple and journalistic language. Here was a free mind, joyfully putting forth his ideas, unconcerned about the reaction of the “professionals”. (*SFS*, p. 115).

""", window_size=80)

    tree = multi_level_summary(chunks, group_size=3, summary_limit=70)
    tree.show_tree_gui()
    caching.save()


def moving_window_decompose(content, window_size=50):
    if len(content) <= window_size:
        return

    split_contents = content.split(" ")
    contents_by_window = []
    overlap = window_size // 2
    for i in range(0, len(split_contents), overlap):
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


def multi_level_summary(chunks: List[str], group_size=3, summary_limit=50):
    layer_lists = [chunks, []]
    parent_dict = {}

    for i_chunk in range(len(chunks)):
        build_bottom_summary(i_chunk, group_size, layer_lists, summary_limit,
                                    parent_dict)
        summarize_higher_summary(group_size, layer_lists, parent_dict,
                                 summary_limit)

    process_remaining_contents(group_size, layer_lists, parent_dict, summary_limit)

    tree = get_tree_of_layer_lists(layer_lists, parent_dict)

    return tree


def summarize_higher_summary(group_size, layer_lists, parent_dict,
                             summary_limit):
    for i_layer in reversed(range(1, len(layer_lists))):

        layer = layer_lists[i_layer]
        # Only summarize when there is group_size contents
        if len(layer) == 0 or len(layer) % group_size != 0:
            continue
        if len(layer_lists) <= i_layer + 1:
            layer_lists.append([])
        next_layer = layer_lists[i_layer + 1]
        # Skip if the group is already summarized
        if len(next_layer) * group_size >= len(layer):
            continue

        summary_to_be_grouped = [(i_layer, len(layer) - group_size + i_summary) for
                                 i_summary in range(group_size)]

        up_context = find_up_context(layer_lists, summary_to_be_grouped[0], group_size)
        summary = summarize_node(summary_to_be_grouped, up_context, layer_lists,
                                 summary_limit)

        next_layer.append(summary)

        new_position = (i_layer + 1, len(next_layer) - 1)

        for position in summary_to_be_grouped:
            parent_dict[position] = new_position


def build_bottom_summary(i_chunk, group_size, layer_lists, summary_limit, parent_dict):
    position = (0, i_chunk)
    up_context = find_up_context(layer_lists, position, group_size)
    summary = summarize_node([position], up_context, layer_lists, summary_limit)
    this_layer, this_position = position
    next_layer = layer_lists[this_layer + 1]
    next_layer.append(summary)
    new_position = (this_layer + 1, len(next_layer) - 1)
    parent_dict[position] = new_position


@auto_cache
def summarize_node(positions, up_context, layer_lists, summary_limit):
    up_context_src = [layer_lists[i_layer][i_summary] for i_layer, i_summary in
                      up_context]
    summary_limit = math.ceil((summary_limit * len(positions)) / 10) * 10
    prompt = f"""
You are trying to summarize the following content into a short summary that is no longer than {summary_limit} words.
"""
    if len(up_context_src) > 0:
        prompt += f"""
The content to be summarized has the following preceding content:
"""
    for i, content in enumerate(up_context_src):
        prompt += f"{i}. {content}\n"

    this_src_list = [layer_lists[this_layer][this_position] for
                     (this_layer, this_position) in positions]
    if len(this_src_list) == 1:
        this_src_in_prompt = this_src_list[0]
    else:
        this_src_in_prompt = "\n".join(
            [f"{i}. {content}" for i, content in enumerate(this_src_list)])

    prompt += f"""
The content to be summarized is:
{this_src_in_prompt}
"""
    prompt += f"""
Please notice that the content to be summarised is a chunk which could be incomplete. You should ignore the incomplete part. Start you answer with `Summary:`.
"""
    chat = Chat(prompt, "You are an helpful assistant who help summarize content.")
    res = chat.complete_chat()
    summary = res[len("Summary:"):].strip()
    return summary


def find_up_context(layer_lists, position, group_size):
    i_layer, in_layer_position = position
    up_context = []
    for i_layer in range(i_layer + 1, len(layer_lists)):
        layer = layer_lists[i_layer]
        remainder = len(layer) % group_size
        start = max(0, len(layer) - remainder - 1)
        for i_summary in range(start, len(layer)):
            up_context.append((i_layer, i_summary))
    return up_context


def process_remaining_contents(group_size, layer_lists, parent_dict, summary_limit):
    no_parent_positions = []
    for i_layer in reversed(range(len(layer_lists))):
        for i_summary in reversed(range(len(layer_lists[i_layer]))):
            position = (i_layer, i_summary)
            if position not in parent_dict:
                no_parent_positions.append(position)
            else:
                break
    while len(no_parent_positions) > 1:
        last_group = no_parent_positions[-group_size:]
        up_context = find_up_context(layer_lists, last_group[0], group_size)
        summary = summarize_node(last_group, up_context, layer_lists, summary_limit)
        this_layer, this_position = last_group[0]
        if len(layer_lists) <= this_layer + 1:
            layer_lists.append([])
        next_layer = layer_lists[this_layer + 1]
        next_layer.append(summary)
        new_position = (this_layer + 1, len(next_layer) - 1)
        for position in last_group:
            parent_dict[position] = new_position
        for i in range(len(last_group)):
            no_parent_positions.pop()
        no_parent_positions.append(new_position)


def get_tree_of_layer_lists(layer_lists, parent_dict):
    tree = Tree()
    pos_node_map = {}
    for i_layer in reversed(range(len(layer_lists))):
        layer = layer_lists[i_layer]
        for i_summary, summary in enumerate(layer):
            position = (i_layer, i_summary)
            if position not in parent_dict:
                new_node = tree.root.s(str(position)).be(summary)
                pos_node_map[position] = new_node
            else:
                parent_position = parent_dict[position]
                parent_node = pos_node_map[parent_position]
                new_node = parent_node.s(str(position)).be(summary)
                pos_node_map[position] = new_node
    return tree


if __name__ == '__main__':
    example()
