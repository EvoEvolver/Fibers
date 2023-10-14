from fibers.tree import Tree
from fibers.testing.testing_trees.loader import load_sample_tree


def test_adding_and_parent():
    tree = Tree("test")
    node1 = tree.new_node_by_path(["a", "b", "c"]).be("test1")
    node2 = tree.add_node_by_path(["a", "b", "d"], "test2")
    node3 = tree.get_node_by_path(["a", "b"]).be("test3")
    assert node1.parent().content == "test3" == node3.content == node2.parent().content


def test_adding_twice():
    tree = Tree("test")
    tree.new_node_by_path(["a", "b", "c"]).be("test1")
    tree.add_node_by_path(["a", "b", "c"], "test2")
    assert tree.get_node_by_path(["a", "b", "c"]).content == "test2"


def test_tree_copy():
    tree = load_sample_tree("dingzhen_world.json")
    tree2 = tree.duplicate_tree_by_node_mapping(lambda node, new_tree: node)
    assert tree2.get_dict_for_prompt() == tree.get_dict_for_prompt()