from fibers.compose.pipeline_text.tree_preprocess import preprocess_text_tree_0

from fibers.helper.cache.cache_service import caching

from fibers.testing.testing_trees import loader

tree = loader.load_sample_tree("scientific_understanding.tex")

tree.show_tree_gui()

preprocess_text_tree_0(tree)

tree.show_tree_gui()

caching.save()