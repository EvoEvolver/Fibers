from fibers.helper.cache.cache_service import caching
from fibers.transform.decorate.text_summary import reset_bad_titles, \
    set_children_summary
from fibers.transform.sparsify.text_sparsify import break_and_merge_siblings, \
    weight_reduce_brutal
from fibers.tree import Tree


def make_summary_and_title(tree: Tree):
    nodes = list(tree.iter_with_dfs())[:-1]
    set_children_summary(tree.root)
    reset_bad_titles(tree.root)

def preprocess_text_tree(tree: Tree):
    break_and_merge_siblings(tree, 100)
    caching.save()
    weight_reduce_brutal(tree, 50)
    caching.save()
    make_summary_and_title(tree)
    caching.save()


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    preprocess_text_tree(tree)
    caching.save_used()
    tree.show_tree_gui()