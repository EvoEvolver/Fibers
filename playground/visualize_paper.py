from fibers.compose.pipeline_text.tree_preprocess import preprocess_text_tree

from fibers.helper.cache.cache_service import caching

from fibers.testing.testing_trees import loader

if __name__ == '__main__':

    tree = loader.load_sample_tree("scientific_understanding.tex")

    preprocess_text_tree(tree)

    tree.show_tree_gui_react()

    caching.save()