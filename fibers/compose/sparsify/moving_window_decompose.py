import html

from fibers.compose.sparsify.shape_optimize import make_all_content_on_leaf
from fibers.data_loader.html_to_tree import html_to_tree
from fibers.testing.testing_nl_dataset.loader import extract_dataset
from fibers.tree import Node
from fibers.tree.node_attr import Attr
from moduler.decorator import example


@example
def main():
    data = extract_dataset("QuALITY.v1.0.1.dev", 1)
    tree = html_to_tree(data["article"], to_markdown=False)
    make_all_content_on_leaf(tree)
    moving_window_decompose(tree.root, window_size=100, overlap_size=50)
    tree.show_tree_gui_react()


class Chunk(Attr):
    def __init__(self, text_before, main_text, text_after, node: Node):
        super().__init__(node)
        self.text_before = text_before
        self.main_text = main_text
        self.text_after = text_after

    def render(self, node: Node, rendered):
        content = f"""
Text before: {html.escape(self.text_before)}<br/>
Main text: {html.escape(self.main_text)}<br/>
Text after: {html.escape(self.text_after)}
"""
        rendered.tabs["Chunk"] = content



def moving_window_decompose(root: Node, window_size=50, overlap_size=10):
    for node in list(root.iter_subtree_with_dfs()):
        if node.has_child():
            continue
        chunks = overlapped_window_decompose(node.content, window_size, overlap_size)
        self_title = node.title()
        num = len(chunks)
        if num == 1:
            continue
        for chunk in reversed(chunks):
            chunk_node = node.new_sibling_after(self_title+" "+str(num)).be(html.escape(chunk[1]))
            Chunk(chunk[0], chunk[1], chunk[2], chunk_node)
            num -= 1
        node.remove_self()


def overlapped_window_decompose(content, window_size, overlap_size):
    if len(content) <= window_size:
        return [("", content, "")]

    split_contents = content.split(" ")
    contents_by_window = []

    for i in range(0, len(split_contents), window_size):
        chunk_end = i + window_size
        chunk_start = i
        if chunk_end > len(split_contents):
            chunk_end = len(split_contents)
        overlap_start = max(0, chunk_start - overlap_size)
        overlap_end = min(len(split_contents), chunk_end + overlap_size)
        main_text = " ".join(split_contents[chunk_start:chunk_end]).strip()
        text_before = " ".join(split_contents[overlap_start:chunk_start]).strip()
        text_after = " ".join(split_contents[chunk_end:overlap_end]).strip()
        contents_by_window.append((text_before, main_text, text_after))

    return contents_by_window





if __name__ == '__main__':
    main()
