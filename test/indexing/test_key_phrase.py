from fibers.data_loader.document import Document
from fibers.indexing.key_phrase import KeyPhraseIndexing

tree_dict = {
    "title": "root",
    "sections": [
        {
            "title": "section 1",
            "content": "Quantum computing can help predict your future"
        },
        {
            "title": "section 2",
            "content": "Numerical analysis is important for fluid dynamics"
        },
        {
            "title": "section 3",
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
    top_node = indexing.get_top_k_nodes("Cohomoogy helps topology", 1)[0]
    assert top_node.content == "Cohomoogy is important for topology"