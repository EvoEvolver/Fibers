from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Tuple

import plotly.graph_objects as go
from hyphen import Hyphenator

from fibers.gui.utlis import hypenate_texts

if TYPE_CHECKING:
    from fibers.tree import Node, Tree
    node_map_type = Callable[[Node], Tuple[str, str] | str]

h_en = Hyphenator('en_US')


def draw_treemap(root: Node):

    ids, labels, parents, texts = prepare_tree_parameters(root)

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        # values=values,
        ids=ids,
        text=texts,
        # text=values,
        root_color="lightgrey",
        # hoverinfo="label+text",
        # hovertemplate="<b>%{label}</b><br>%{hovertext}",
        texttemplate="<b>%{label}</b><br>%{text}",
        hovertemplate="<b>%{label}</b><br>%{text}<extra></extra>",
        hoverinfo="text",
        # marker=dict(cornerradius=5)
    ))

    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    # fig.update_traces(marker=dict(cornerradius=5))
    fig.show()


def get_json_for_treemap(root: Node):
    ids, labels, parents, texts = prepare_tree_parameters(root)
    node_list = []
    for i in range(len(ids)):
        node_list.append({
            "id": ids[i],
            "label": labels[i],
            "parent": parents[i],
            "text": texts[i]
        })
    return node_list


def prepare_tree_parameters(root: Node):
    tree = root.tree
    labels = []
    parents = []
    texts = []
    ids = []
    add_node_to_list(labels, parents, texts, ids, root, tree)
    line_width = 40
    for i in range(len(texts)):
        if len(texts[i].strip()) == 0:
            continue
        texts[i] = hypenate_texts(texts[i], line_width)
        labels[i] = hypenate_texts(labels[i], line_width)
    return ids, labels, parents, texts


def add_node_to_list(labels, parents, values, ids, node: Node, tree: Tree):
    i = 1
    children = tree.get_children_dict(node)
    for key, child in children.items():
        node_path = tree.get_node_path(child)
        value = child.content
        label = child.title()
        label = str(i) + ". " + key if len(children) > 1 else label
        labels.append(label)
        values.append(value)
        parents.append("/".join(node_path[:-1]))
        ids.append("/".join(node_path))
        add_node_to_list(labels, parents, values, ids, child, tree)
        i += 1
