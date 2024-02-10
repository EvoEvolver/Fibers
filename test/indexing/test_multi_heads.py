from fibers.data_loader.document import Document
from fibers.indexing.indexing import VectorIndexing

tree_dict = {
    "title": "root",
    "sections": [
        {
            "title": "apple",
            "content": "banana"
        },
        {
            "title": "banana",
            "content": "headset"
        },
        {
            "title": "India",
            "content": "Mike"
        }
    ],
    "content": "University of Toronto"
}


def test_multi_similarity():
    tree = Document.from_dict(tree_dict).to_tree()

    def get_weighted_contents(node):
        return [(node.content, 0.5), (node.title(), 0.5)]

    indexing = VectorIndexing(tree.all_nodes(), get_weighted_contents)
    top_node = indexing.get_top_k_nodes(["apple", "banana"], 5)
    assert top_node[0].content == "banana"
    assert top_node[1].content == "headset"
