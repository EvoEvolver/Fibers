import re

import html2text
import requests
from bs4 import BeautifulSoup

from fibers.data_loader.document import Document


def url_to_doc(url: str) -> Document:
    html = requests.get(url).text
    doc = html_to_doc(html)
    return doc


def html_to_doc(html: str) -> Document:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title").text
    root = extract_article_root(soup)
    doc = html_to_raw_doc(root, title=title)
    html_to_markdown(doc)
    return doc


def html_to_raw_doc(soup: BeautifulSoup, title=""):
    hn_pattern = re.compile(r"h[1-6]")
    curr_doc = Document(title, "", [])
    root_doc = curr_doc
    doc_stack = []
    curr_content = []
    curr_level = -1
    for child in soup.children:
        # check whether it's hn use regex
        if child.name and hn_pattern.match(child.name):
            curr_doc.content = ("\n".join(curr_content)).strip()
            this_level = int(child.name[1])
            new_doc = Document(child.text, "", [])
            if this_level > curr_level:
                curr_doc.sections.append(new_doc)
                doc_stack.append((curr_doc, this_level))
            else:
                while len(doc_stack) > 0 and doc_stack[-1][1] > this_level:
                    doc_stack.pop()
                doc_stack[-1][0].sections.append(new_doc)

            curr_content = []
            curr_level = this_level
            curr_doc = new_doc

        else:
            curr_content.append(str(child))
    curr_doc.content = "\n".join(curr_content)
    return root_doc


def bfs_on_soup(soup: BeautifulSoup):
    queue = [([], soup)]  # queue of (path, element) pairs
    while queue:
        path, element = queue.pop(0)
        if hasattr(element, 'children'):  # check for leaf elements
            for child in element.children:
                if child.name in ["html", "body", "div", "article", "main"]:
                    queue.append(
                        (path + [child.name if child.name is not None else type(child)],
                         child))
                    print(queue[-1][0])
                    yield path, child


def extract_article_root(soup: BeautifulSoup):
    """
    Extract the element with most article related elements, including p, h1, h2, h3, h4, h5, h6
    """
    n_article_elements = []
    elements = []
    for path, element in bfs_on_soup(soup):
        if element.name in ["div", "article"]:
            elements.append(element)
            # count the number of article related elements
            n_article_elements_here = 0
            for child in element.children:
                if child.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6"]:
                    n_article_elements_here += 1
            n_article_elements.append(n_article_elements_here)
    # find the div with the most article related elements
    max_n_article_elements = max(n_article_elements)
    max_n_article_elements_index = n_article_elements.index(max_n_article_elements)
    article_root = elements[max_n_article_elements_index]
    return article_root


html2text_hanlder = html2text.HTML2Text()
html2text_hanlder.ignore_links = True
html2text_hanlder.ignore_images = True


def html_to_markdown(doc: Document):
    doc.content = html2text_hanlder.handle(doc.content)
    for section in doc.sections:
        html_to_markdown(section)


if __name__ == "__main__":
    doc = url_to_doc("https://plato.stanford.edu/entries/feyerabend/")
    doc.to_tree().show_tree_gui()
