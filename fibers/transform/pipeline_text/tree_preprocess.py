from fibers.helper.cache.cache_service import cache_service
from fibers.transform.decorate.text_summary import reset_bad_titles, add_children_summary
from fibers.transform.sparsify.text_sparsify import break_and_merge_siblings, \
    weight_reduce_brutal
from fibers.tree import Tree


def make_summary_and_title(tree: Tree):
    nodes = list(tree.iter_with_dfs())[:-1]
    changed_nodes, summary_list = add_children_summary(nodes)
    for node, summary in zip(changed_nodes, summary_list):
        node.be(summary)
    reset_bad_titles(nodes)

def preprocess_text_tree(tree: Tree):
    break_and_merge_siblings(tree, 100)
    cache_service.save_cache()
    weight_reduce_brutal(tree, 50)
    cache_service.save_cache()
    make_summary_and_title(tree)
    cache_service.save_cache()


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_tree
    tree = load_sample_tree("Feyerabend.md")
    preprocess_text_tree(tree)
    cache_service.save_used_cache()
    tree.show_tree_gui()