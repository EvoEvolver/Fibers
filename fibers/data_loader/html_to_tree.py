import base64
import re
from typing import List

import html2text
import requests
from bs4 import BeautifulSoup

from fibers.data_loader.bad_text_node_class import add_bad_reason
from fibers.tree import Tree, Node


def url_to_tree(url: str) -> Tree:
    html = requests.get(url).text
    return html_to_tree(html)


def html_to_tree(html: str, to_markdown=False) -> Tree:
    soup = BeautifulSoup(html, "html.parser")
    pre_process_html_tree(soup)
    title = soup.find("title")
    if title:
        title = title.text
    else:
        title = ""
    root = extract_article_root(soup)
    tree = html_to_raw_tree(root, title=title)
    if to_markdown:
        html_to_markdown(tree.root)
    post_process_html_tree(tree)
    return tree


def pre_process_html_tree(soup: BeautifulSoup):
    for script in soup(["script", "style"]):
        # remove all javascript and stylesheet code
        script.decompose()

def image_to_base64_on_tree(tree: Tree):
    for node in tree.all_nodes():
        soup = BeautifulSoup(node.content, "html.parser")
        image_to_base64(soup)
        node.content = str(soup)

def image_to_base64(soup: BeautifulSoup):
    img_elements = soup.find_all("img")
    for img_element in img_elements:
        # get src of img element
        src = img_element.get("src")
        # open image file
        with open(src, "rb") as f:
            # convert image to base64
            base64_img = base64.b64encode(f.read()).decode("utf-8")
            # replace src with base64
            img_element["src"] = f"data:image/png;base64,{base64_img}"

def post_process_html_tree(tree):
    for node in tree.all_nodes():
        node.content = "<span>" + node.content + "</span>"



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
                new_node = curr_node.s(child.text.strip())
                node_stack.append((curr_node, this_level))
            else:
                while len(node_stack) > 0 and node_stack[-1][1] > this_level:
                    node_stack.pop()
                parent_node = node_stack[-1][0]
                new_node = parent_node.s(child.text.strip())

            curr_content = []
            curr_level = this_level
            curr_node = new_node
        else:
            curr_content.append(child)
    set_content(curr_node, curr_content)

    return tree

segment_length_threshold = 1500

def set_content(node: Node, contents: List):
    segment_contents = [""]
    for segment in contents:
        # judge if element is <p>
        if hasattr(segment, "name"):
            if segment.name in ["p", "ul", "ol", "blockquote", "pre"]:
                segment = str(segment)
            else:
                segment = str(segment)
        else:
            segment = str(segment)
        if len(segment.strip()) == 0:
            continue
        segment_contents.append(segment)

    if segment_contents[0] == "":
        segment_contents.pop(0)

    for i, segment in enumerate(segment_contents):
        node_added = node.s(f"Segment {i+1}").be(segment)
        add_bad_reason(node_added, "overlap_to_sibling")
        add_bad_reason(node_added, "bad_title")


def bfs_on_soup(soup: BeautifulSoup):
    queue = [([], soup)]  # queue of (path, element) pairs
    while queue:
        path, element = queue.pop(0)
        if hasattr(element, 'children'):  # check for leaf elements
            for child in element.children:
                if child.name in ["html", "body", "div", "article", "main", "span"]:
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
        if element.name in ["div", "article", "html", "body", "main"]:
            elements.append(element)
            # count the number of article related elements
            n_article_elements_here = 0
            for child in element.children:
                if child.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"]:
                    n_article_elements_here += 1
            n_article_elements.append(n_article_elements_here)
            #print(n_article_elements_here, element.name, element.get("class"), element.get("id"))
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
    doc.show_tree_gui_old()
