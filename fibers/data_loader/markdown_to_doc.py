import markdown
from bs4 import BeautifulSoup

from fibers.data_loader.document import Document
from fibers.data_loader.html_to_doc import html_to_raw_doc, html_to_markdown


def markdown_to_doc(src: str, title="") -> Document:
    html = markdown.markdown(src)
    soup = BeautifulSoup(html, "html.parser")
    doc = html_to_raw_doc(soup, title=title)
    html_to_markdown(doc)
    return doc

if __name__ == "__main__":
    from fibers.testing.testing_trees.loader import load_sample_src
    src = load_sample_src("Feyerabend.md")
    doc = markdown_to_doc(src)
    doc.show_tree_gui()