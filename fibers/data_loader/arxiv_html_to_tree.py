import base64
import html
import os
import re
from multiprocessing import freeze_support
from typing import List

import html2text
import requests
from bs4 import BeautifulSoup, PageElement
from bs4 import Tag

from fibers.data_loader.bad_text_node_class import add_bad_reason
from fibers.tree import Node
from fibers.tree.node_attr import Attr

# arxiv_url = "https://arxiv.org/html/2401.11314v2"

# arxiv_url = "https://arxiv.org/html/2404.04326v1"

arxiv_url = "https://arxiv.org/html/2406.07003v1"


class ArxivNode(Node):
    def __init__(self, source: BeautifulSoup | Tag, id: str, label: str, title: str = "", content: str = ""):
        super().__init__(title, content)
        self._label: str = label
        self._id: str = id
        self._html_soup: BeautifulSoup = source

    def get_label(self) -> str:
        return self._label

    def get_id(self) -> str:
        return self._id

    def get_soup(self) -> BeautifulSoup:
        return self._html_soup


def replace_math_with_tex(soup: BeautifulSoup):
    for tag in soup.find_all("math", recursive=True):
        if not isinstance(tag, Tag):
            continue
        latex = tag.get("alttext")
        alt_tag = soup.new_tag("tex")
        if latex is not None:
            alt_tag.string = latex
            tag.replace_with(alt_tag)
        else:
            tag.decompose()


def pre_process_html_tree(soup: BeautifulSoup):
    for script in soup(["script", "style"]):
        # remove all javascript and stylesheet code
        script.decompose()


def get_abstract_node(rootSoup: BeautifulSoup) -> ArxivNode:
    source = rootSoup.find('div', class_="ltx_abstract", recursive=True)
    content_wraper = source.find('p', class_='ltx_p')
    return ArxivNode(source, content_wraper.get('id'), "abstract", "Abstract", content_wraper.text)


def get_section_nodes(rootSoup: BeautifulSoup) -> list[ArxivNode]:
    children = []
    for section in rootSoup.find_all('section', class_='ltx_section', recursive=True):
        if not re.match(r'^S\d+$', section['id']):
            continue
        print(f"section: {section['id']}")

        Section = ArxivNode(section, section['id'], "section",
                            section.find_all_next('h2', class_="ltx_title ltx_title_section")[0].text, "")
        build_tree(Section)
        children.append(Section)
        print("----------")
    return children


def get_subsection_nodes(sectionSoup: BeautifulSoup) -> list[ArxivNode]:
    global arxiv_url
    children = []
    index_para = 1
    index_figure = 1
    for i, e in enumerate(sectionSoup.children):

        if not isinstance(e, Tag):
            continue
        class_ = e.get('class')
        print(i, e.name, class_)
        if e.name == 'div' and 'ltx_para' in class_:
            if not re.match(r'^S\d+\.p.$', e['id']):
                continue
            print(f"section: {e['id']}")
            # print(section)
            Paragraph = ArxivNode(e, e['id'], "paragraph",
                                  "paragraph " + str(index_para),
                                  '<!DOCTYPE html><meta content=\"text/html; charset=utf-8\" http-equiv=\"content-type\"/>' + e.__str__())
            children.append(Paragraph)
            index_para += 1
        elif e.name == 'section' and 'ltx_subsection' in class_:
            if not re.match(r'^S\d+\.SS\d+$', e['id']):
                continue
            print(f"section: {e['id']}")
            # print(section)
            SubSection = ArxivNode(e, e['id'], "subsection",
                                   e.find('h3', class_="ltx_title ltx_title_subsection").text, "")
            build_tree(SubSection)
            children.append(SubSection)

            print("----------")
        elif e.name == 'figure':
            image_tags = e.find_all('img', class_='ltx_graphics', recursive=True)
            for image_tag in image_tags:
                if image_tag is not None and isinstance(image_tag, Tag):
                    if 'src' in image_tag.attrs:
                        image_tag['src'] = arxiv_url + '/' + image_tag['src']
                    if 'width' in image_tag.attrs and 'height' in image_tag.attrs:
                        # Make sure the image fit in the window
                        w, h = int(image_tag['width']), int(image_tag['height'])
                        div_max_width = 500
                        if w > div_max_width:
                            image_tag['width'] = str(div_max_width)
                            image_tag['height'] = f"{int(h * (div_max_width / w))}"
                            image_tag['style'] = "object-fit: contain;"

            Figure = ArxivNode(e, e['id'], "figure", "figure " + str(index_figure), e.__str__())
            # Figure = ArxivNode(e, e['id'], "figure", "figure " + str(index_figure), re.sub(r"\"([^\"]+)\.(png|jpg)\"", regrex_str, e.__str__()))
            children.append(Figure)
            index_figure += 1
    return children


def remove_tag(html_str, tag):
    import re

    pattern = rf'<{tag}[^>]*>.*?</{tag}>'
    return re.sub(pattern, '', html_str)


def get_paragraph_nodes(subsectionSoup: BeautifulSoup) -> list[ArxivNode]:
    children = []
    index_para = 1
    index_figure = 1
    for i, e in enumerate(subsectionSoup.children):
        if not isinstance(e, Tag):
            continue
        class_ = e.get('class')
        print(i, e.name, class_)
        if e.name == 'div' and ('ltx_para' in class_ or 'ltx_theorem' in class_):
            # if not re.match(r'^S\d+\.SS\d+\.p.$', e['id']):
            #     continue
            print(f"section: {e['id']}")
            # print(section)
            Paragraph = ArxivNode(e, e['id'], "paragraph",
                                  "paragraph " + str(index_para),
                                  '<!DOCTYPE html><meta content=\"text/html; charset=utf-8\" http-equiv=\"content-type\"/>' + e.__str__())
            children.append(Paragraph)
            index_para += 1

            print("----------")
        elif e.name == 'figure':
            # if not re.match(r'^S\d+\.SS\d+\.F\d+$', e['id']) and not re.match(r'alg\d+', e['id']):
            #     continue
            image_tags = e.find_all('img', class_='ltx_graphics', recursive=True)
            for image_tag in image_tags:
                if image_tag is not None and isinstance(image_tag, Tag):
                    if 'src' in image_tag.attrs:
                        image_tag['src'] = arxiv_url + '/' + image_tag['src']
                    if 'width' in image_tag.attrs and 'height' in image_tag.attrs:
                        # Make sure the image fit in the window
                        w, h = int(image_tag['width']), int(image_tag['height'])
                        div_max_width = 500
                        if w > div_max_width:
                            image_tag['width'] = str(div_max_width)
                            image_tag['height'] = f"{int(h * (div_max_width / w))}"
                            image_tag['style'] = "object-fit: contain;"

            Figure = ArxivNode(e, e['id'], "figure", "figure " + str(index_figure), e.__str__())

            children.append(Figure)
            index_figure += 1

    return children


def build_tree(parent: ArxivNode):
    if parent.get_id() == "root":
        title = parent.get_soup().find('h1', class_="ltx_title ltx_title_document", recursive=True)
        if title is None:
            raise Exception("Can't resolve title")
        title = title.text
        parent.title = title

        author = parent.get_soup().find('div', class_="ltx_authors", recursive=True)
        if author is None:
            print("Can't resolve author")
        else:
            parent.content = author.__str__()

        Abstract = get_abstract_node(parent.get_soup())
        parent.add_child(Abstract)
        Abstract.set_children(get_section_nodes(parent.get_soup()))

    elif parent.get_label() == "section":
        parent.set_children(get_subsection_nodes(parent.get_soup()))
    elif parent.get_label() == "subsection":
        parent.set_children(get_paragraph_nodes(parent.get_soup()))
    return


def url_to_tree(url: str) -> ArxivNode:
    global arxiv_url
    arxiv_url = url
    html_source = requests.get(url).text
    # try:
    #     with open("cached_page.html", "r", encoding="utf-8") as f:
    #         html_source = f.read()
    # except FileNotFoundError:
    #     print("Error: Cached HTML file not found.")
    soup = BeautifulSoup(html_source, "html.parser")
    replace_math_with_tex(soup)
    pre_process_html_tree(soup)
    head = ArxivNode(soup, "root", "root", "", "")
    build_tree(head)
    return head


if __name__ == '__main__':
    # html_source = requests.get("https://arxiv.org/html/2404.04326v1").text
    # with open("cached_page.html", "w", encoding="utf-8") as f:
    #     f.write(html_source)
    head = url_to_tree(arxiv_url)
    head.display(dev_mode=True)
    # # sleep for 10 seconds to keep the server running
    import time

    while True:
        time.sleep(1)
