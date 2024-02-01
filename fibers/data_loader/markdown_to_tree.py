import markdown
from bs4 import BeautifulSoup

from fibers.data_loader.html_to_tree import html_to_raw_tree, html_to_markdown
from fibers.tree import Tree


def markdown_to_tree(src: str, title="") -> Tree:
    html = markdown.markdown(src)
    soup = BeautifulSoup(html, "html.parser")
    tree = html_to_raw_tree(soup, title=title)
    return tree

if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_src
    src = load_sample_src("Feyerabend.md")
    tree = markdown_to_tree(src)
    tree.show_tree_gui_old()