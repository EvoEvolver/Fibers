from fibers.transform.sparsify.text_sparsify import weight_reduce_brutal

from fibers.helper.cache.cache_service import cache_service

from fibers.testing.testing_trees import loader

tree = loader.load_sample_tree("scientific_understanding.tex")

tree.show_tree_gui()

weight_reduce_brutal(tree, 300)

tree.show_tree_gui()

cache_service.save_cache()