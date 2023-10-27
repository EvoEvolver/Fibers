from fibers.transform.pipeline_text.tree_preprocess import preprocess_text_tree

from fibers.helper.cache.cache_service import cache_service

from fibers.testing.testing_trees import loader

tree = loader.load_sample_tree("scientific_understanding.tex")

tree.show_tree_gui()

preprocess_text_tree(tree)

tree.show_tree_gui()

cache_service.save_cache()