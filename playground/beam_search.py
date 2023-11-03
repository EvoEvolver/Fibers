from fibers import transform
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.helper.cache.cache_service import caching
from fibers.transform.decorate.code_summary import CodeSummarizedNodeClass, \
    summarize_code_tree
from fibers.transform.extract.code_searcher import code_beam_searcher
from fibers.tree.node import ContentMap
from fibers.tree.prompt_utils import get_node_list_prompt

tree = get_tree_for_module(transform)

summarize_code_tree(tree)

content_map = ContentMap(lambda n: CodeSummarizedNodeClass.get_summary(n) or n.content)

nodes_related = code_beam_searcher(tree.root, "The function is to summarize code content.", "function", content_map)

print(get_node_list_prompt(nodes_related))

caching.save_used()