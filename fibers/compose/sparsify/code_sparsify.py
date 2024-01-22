import inspect

from fibers.compose.sparsify.text_sparsify import count_words
from fibers.tree import Node
from fibers.tree.node_class.code_node import get_type, get_docs, get_obj, CodeNodeClass


def count_lines(string):
    return len(string.split("\n"))


def count_function_class_lines(node: Node):
    if get_type(node) == "section":
        return count_lines(node.content), 0
    docs = get_docs(node)
    obj = get_obj(node)
    n_docs_lines = count_lines(docs)
    try:
        obj_src = inspect.getsource(obj)
    except:
        obj_src = ""
    n_body_line = count_lines(obj_src) - n_docs_lines
    if n_body_line<0:
        pass
    n_docs_words = count_words(docs)
    return n_body_line, n_docs_words


def count_children(node: Node):
    return len(node.children())


def get_fat_nodes(root: Node, doc_word_limit=50, code_col_limit=100):
    for node in root.iter_subtree_with_bfs():
        if node.isinstance(CodeNodeClass):
            n_body_line, n_docs_words = count_function_class_lines(node)
            if n_docs_words > doc_word_limit:
                yield node
                continue
            if get_type(
                    node) == "function" and n_body_line > code_col_limit:
                yield node


if __name__ == '__main__':
    import fibers
    from fibers.data_loader.module_to_tree import get_tree_for_module

    tree = get_tree_for_module(fibers)
    fat_nodes = get_fat_nodes(tree.root)
    for node in fat_nodes:
        print(node.path(), count_function_class_lines(node))
