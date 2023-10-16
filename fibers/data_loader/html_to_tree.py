import re
from typing import List

import html2text
import requests
from bs4 import BeautifulSoup

from fibers.tree import Tree, Node


def url_to_tree(url: str) -> Tree:
    html = requests.get(url).text
    return html_to_tree(html)


def html_to_tree(html: str) -> Tree:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title").text
    root = extract_article_root(soup)
    tree = html_to_raw_tree(root, title=title)
    html_to_markdown(tree.root)
    return tree


def html_to_raw_tree(soup: BeautifulSoup, title="") -> Tree:
    hn_pattern = re.compile(r"h[1-6]")
    tree = Tree()
    curr_node = tree.root.s(title)
    node_stack = []
    curr_content = []
    curr_level = -1
    for child in soup.children:
        # check whether it's hn use regex
        if hasattr(child, "name") and child.name and hn_pattern.match(child.name):
            set_content(curr_node, curr_content)
            this_level = int(child.name[1])
            if this_level > curr_level:
                new_node = curr_node.s(child.text)
                node_stack.append((curr_node, this_level))
            else:
                while len(node_stack) > 0 and node_stack[-1][1] > this_level:
                    node_stack.pop()
                parent_node = node_stack[-1][0]
                new_node = parent_node.s(child.text)

            curr_content = []
            curr_level = this_level
            curr_node = new_node
        else:
            curr_content.append(str(child))
    set_content(curr_node, curr_content)

    return tree


def set_content(node: Node, contents: List):
    n_segments = 0
    for segment in contents:
        if len(segment.strip()) == 0:
            continue
        n_segments += 1
        node_added = node.s(f"Segment {n_segments}").be(segment)
        node_added.meta["overlap_to_sibling"] = True


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


html2text_handler = html2text.HTML2Text()
html2text_handler.ignore_links = True
html2text_handler.ignore_images = True


def html_to_markdown(root: Node):
    root.content = html2text_handler.handle(root.content)
    for child in root.children().values():
        html_to_markdown(child)


if __name__ == "__main__":
    doc = url_to_tree("https://plato.stanford.edu/entries/feyerabend/")
    doc.show_tree_gui()
