import markdown
from bs4 import BeautifulSoup

from fibers.data_loader.html_to_tree import html_to_raw_tree, html_to_markdown
from fibers.tree import Node


def markdown_to_tree(src: str, title="", keep_markdown=False) -> Node:
    html = markdown.markdown(src)
    soup = BeautifulSoup(html, "html.parser")
    root = html_to_raw_tree(soup, title=title)
    if keep_markdown:
        html_to_markdown(root)
    return root


if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_src

    src = load_sample_src("Feyerabend.md")
    root = markdown_to_tree(src)
    root.display()
