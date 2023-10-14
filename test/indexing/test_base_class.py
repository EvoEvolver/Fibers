from fibers.data_loader.document import Document
from fibers.indexing import Indexing

tree_dict = {
    "title": "root",
    "sections": [
        {
            "title": "section 1",
            "content": "banana"
        },
        {
            "title": "section 2",
            "content": "headset"
        },
        {
            "title": "section 3",
            "content": "Mike"
        }
    ],
    "content": "University of Toronto"
}


def test_similarity():
    tree = Document.from_dict(tree_dict).to_tree()
    indexing = Indexing(tree.all_nodes())
    top_node = indexing.get_top_k_nodes("pear", 1)[0]
    assert top_node.content == "banana"
    top_node = indexing.get_top_k_nodes("headset", 1)[0]
    assert top_node.content == "headset"
    top_node = indexing.get_top_k_nodes("Jack", 1)[0]
    assert top_node.content == "Mike"
    top_node = indexing.get_top_k_nodes("University of Calgary", 1)[0]
    assert top_node.content == "University of Toronto"


def test_add():
    tree = Document.from_dict(tree_dict).to_tree()
    indexing = Indexing(tree.all_nodes())
    new_node = tree.new_node_by_path(["root", "section 4"])
    new_node.content = "China"
    indexing.add_nodes([new_node])
    top_node = indexing.get_top_k_nodes("United states", 1)[0]
    assert top_node.content == "China"
    top_node = indexing.get_top_k_nodes("Jack", 1)[0]
    assert top_node.content != "China"

def test_remove_a_little():
    tree = Document.from_dict(tree_dict).to_tree()
    indexing = Indexing(tree.all_nodes())
    node = tree.get_node_by_path(["root", "section 1"])
    indexing.remove_nodes([node])
    top_node = indexing.get_top_k_nodes("pear", 1)[0]
    assert top_node.content != "banana"

def test_remove_a_lot():
    tree = Document.from_dict(tree_dict).to_tree()
    indexing = Indexing(tree.all_nodes())
    nodes = tree.all_nodes()[2:]
    indexing.remove_nodes(nodes)
    top_node = indexing.get_top_k_nodes("pear", 1)[0]
    assert top_node.content != "banana"
