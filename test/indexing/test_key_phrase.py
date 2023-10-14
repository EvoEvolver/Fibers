from fibers.data_loader.document import Document
from fibers.helper.cache.cache_service import cache_service
from fibers.indexing.key_phrase import KeyPhraseIndexing

cache_service.set_main_here()

tree_dict = {
    "title": "root",
    "sections": [
        {
            "title": "Quantum computing",
            "content": "Quantum computing can help predict your future"
        },
        {
            "title": "Numerical analysis",
            "content": "Numerical analysis is vital for fluid dynamics"
        },
        {
            "title": "Cohomoogy",
            "content": "Cohomoogy is important for topology"
        },
    ]
}

def test_search():
    tree = Document.from_dict(tree_dict).to_tree()
    #with refresh_cache():
    indexing = KeyPhraseIndexing(tree.all_nodes())
    top_node = indexing.get_top_k_nodes("Quantum computing", 1)[0]
    assert top_node.content == "Quantum computing can help predict your future"
    top_node = indexing.get_top_k_nodes("Cohomoogy", 1)[0]
    assert top_node.content == "Cohomoogy is important for topology"