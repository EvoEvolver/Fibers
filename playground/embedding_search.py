from fibers import tree as tree_module
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.indexing.parent_mixed import ParentMixedIndexing
from fibers.transform.decorate.code_summary import summarize_code_tree, \
    CodeSummarizedNodeClass
from fibers.tree.node import ContentMap
from fibers.tree.prompt_utils import get_node_list_prompt

tree = get_tree_for_module(tree_module)
summarize_code_tree(tree)

content_map = ContentMap(lambda n: CodeSummarizedNodeClass.get_summary(n) or n.content)

indexing = ParentMixedIndexing(tree.all_nodes(), content_map)

top_nodes = indexing.get_top_k_nodes(("Tree",
                                      "The class Tree stores node information, including the path of each node, and allows for operations such as retrieving node information, manipulating nodes, visualizing the tree, extracting sub-trees, iterating through the tree, and persisting the tree."),
                                     10)
print(get_node_list_prompt(top_nodes, content_map))