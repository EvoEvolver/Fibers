from moduler.decorator import example

from fibers.helper.cache.cache_service import caching
from fibers.transform.decorate.text_summary import reset_bad_titles, \
    set_children_summary
from fibers.transform.decorate.tree_map import node_map_with_dependency
from fibers.transform.densify.merge_small_nodes import deal_single_child_for_node, \
    deal_single_child
from fibers.transform.sparsify.text_sparsify import break_and_merge_siblings, \
    weight_reduce_brutal
from fibers.tree import Tree


def make_summary_and_title(tree: Tree):
    set_children_summary(tree.root)
    reset_bad_titles(tree.root)


def preprocess_text_tree_0(tree: Tree, fat_limit=100):
    break_and_merge_siblings(tree, fat_limit)
    caching.save()
    weight_reduce_brutal(tree, fat_limit)
    caching.save()
    make_summary_and_title(tree)
    caching.save()


def break_long_nodes(tree, fat_limit):
    pass


def preprocess_text_tree_1(tree: Tree, fat_limit=100):
    break_long_nodes(tree, fat_limit)

@example
def example_usage():
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    preprocess_text_tree_0(tree)
    caching.save_used()
    tree.show_tree_gui()


if __name__ == '__main__':
    example_usage()
