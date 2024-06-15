import base64
import html
import os
import re
from typing import List

import html2text
import requests
from bs4 import BeautifulSoup, PageElement

from fibers.data_loader.bad_text_attr import BadText
from fibers.tree import Node
from fibers.tree.node_attr import Attr


class SoupInfo(Attr):
    def __init__(self, soup: BeautifulSoup, node: Node):
        super().__init__(node)
        self.soup = soup

    @staticmethod
    def soup_to_content(root: Node):
        for node in root.iter_subtree_with_dfs():
            node.content = str(SoupInfo.get(node).soup)


def url_to_tree(url: str) -> Node:
    html = requests.get(url).text
    return html_to_tree(html)


def html_to_tree(html: str, to_markdown=False) -> Node:
    soup = BeautifulSoup(html, "html.parser")
    pre_process_html_tree(soup)
    title = soup.find("title")
    if title:
        title = title.text
    else:
        title = ""
    root = extract_article_root(soup)
    root = html_to_raw_tree(root, title=title)
    init_soup_info(root)
    if to_markdown:
        html_to_markdown(root)
    return root


def init_soup_info(root: Node):
    for node in root.iter_subtree_with_dfs():
        soup = BeautifulSoup(node.content, "html.parser")
        if node.has_attr(SoupInfo):
            node.get_attr(SoupInfo).soup = soup
        else:
            SoupInfo(soup, node)


def pre_process_html_tree(soup: BeautifulSoup):
    for script in soup(["script", "style"]):
        # remove all javascript and stylesheet code
        script.decompose()


def remove_attrs(root: Node, attrs_to_keep: List[str]):
    for node in root.iter_subtree_with_dfs():
        soup = SoupInfo.get(node).soup
        for ele in soup.descendants:
            if ele.name:
                for attr in list(ele.attrs):
                    if attr not in attrs_to_keep:
                        del ele.attrs[attr]
        node.content = html.escape(str(soup))

def remove_elements(root: Node, elements: List[str]):
    for node in root.iter_subtree_with_dfs():
        soup = SoupInfo.get(node).soup
        for ele in soup.find_all(elements):
            ele.decompose()
        node.content = str(soup)


def unwrap_elements(root: Node, elements: List[str]):
    for node in root.iter_subtree_with_dfs():
        soup = SoupInfo.get(node).soup
        for ele in soup.find_all(elements):
            ele.unwrap()
        node.content = str(soup)


def image_to_base64_on_tree(root: Node, base_path=""):
    for node in root.iter_subtree_with_dfs():
        soup = SoupInfo.get(node).soup
        image_to_base64(soup, base_path)

def image_to_base64(soup: BeautifulSoup, base_path):
    img_elements = soup.find_all("img")
    for img_element in img_elements:
        # get src of img element
        src = img_element.get("src")
        if src.startswith("data:image"):
            continue
        src = os.path.join(base_path, src)
        # open image file
        with open(src, "rb") as f:
            # convert image to base64
            base64_img = base64.b64encode(f.read()).decode("utf-8")
            # replace src with base64
            img_element["src"] = f"data:image/png;base64,{base64_img}"



def html_to_raw_tree(soup: BeautifulSoup, title="") -> Node:
    hn_pattern = re.compile(r"h[1-6]")
    root = Node()
    curr_node = root.s(title)
    node_stack = []
    curr_content: List[PageElement] = []
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

    return root

def set_content(node: Node, contents: List[PageElement]):
    segment_contents = [""]
    for segment in contents:
        segment = unwrap_useless_tags(segment)
        segment = str(segment)
        if len(segment.strip()) == 0:
            continue
        segment_contents.append(segment)

    if segment_contents[0] == "":
        segment_contents.pop(0)

    for i, segment in enumerate(segment_contents):
        node_added = node.s(f"Segment {i+1}").be(segment)
        bad_text_attr = BadText.get(node_added)
        bad_text_attr.add_bad_reason("overlap_to_sibling")
        bad_text_attr.add_bad_reason("bad_title")


def unwrap_useless_tags(content: PageElement):
    if content.name in ["p", "div", "span"]:
        # return all children
        if len(content.contents) == 1:
            return unwrap_useless_tags(content.contents[0])
        return "".join([str(child) for child in content.children])
    return content


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
    for child in root.children():
        html_to_markdown(child)


if __name__ == "__main__":
    doc = url_to_tree("https://scholar.google.com/scholar_case?case=16062632215534775045&q=trump&hl=en&as_sdt=2006")
    doc.display()
