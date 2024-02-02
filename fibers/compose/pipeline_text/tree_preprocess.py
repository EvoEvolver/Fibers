from fibers.compose.sparsify.shape_optimize import merge_single_child_into_parent
from moduler.decorator import example

from fibers.helper.cache.cache_service import caching
from fibers.compose.decorate.text_summary import reset_bad_titles, set_content_summary
from fibers.compose.sparsify.text_sparsify import break_and_merge_siblings, \
    weight_reduce_brutal, reduce_max_children_number
from fibers.tree import Tree


def make_summary_and_title(tree: Tree):
    set_content_summary(tree.root)
    reset_bad_titles(tree.root)


def preprocess_text_tree(tree: Tree, fat_limit=100):
    merge_single_child_into_parent(tree.root)
    break_and_merge_siblings(tree)
    weight_reduce_brutal(tree, fat_limit)
    merge_single_child_into_parent(tree.root)
    reset_bad_titles(tree.root.first_child())
    set_content_summary(tree.root.first_child(), "The summary should be about 50 words")
    caching.save()


@example
def example_usage():
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    preprocess_text_tree(tree)
    caching.save_used()
    tree.show_tree_gui_react()


if __name__ == '__main__':
    example_usage()
