from fibers.data_loader.bad_text_node_class import has_bad_reason
from fibers.tree import Node


def merge_single_child_into_parent(root: Node):
    if root is root.tree.root:
        root = root.first_child()
    for node in list(root.iter_subtree_with_dfs()):
        if not node.is_empty():
            continue
        if len(node.children()) == 1:
            child = node.first_child()
            if has_bad_reason(child, "bad_title"):
                node.content += child.content
                for key, child_child in child.children():
                    child_child.reset_path(node.path() + (key,))
                child.remove_self()


