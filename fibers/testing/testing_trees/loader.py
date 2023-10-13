import os

from fibers.data_loader.document import Document
from fibers.tree import Tree
from fibers.transform.build_from_sections import tree_from_doc

curr_dir = os.path.dirname(os.path.abspath(__file__))


def load_sample_tree(path: str) -> Tree:
    """
    Args:
        path: The relative path to the json file.

    Returns:
        The tree loaded from the json file.
    """
    if not path.endswith(".json"):
        path += ".json"
    doc = Document.from_json(os.path.join(curr_dir, path))
    tree = tree_from_doc(doc, {'title': doc.title})
    return tree
