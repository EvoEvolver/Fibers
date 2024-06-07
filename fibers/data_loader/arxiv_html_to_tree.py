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


class ArxivNode(Node):
    def __init__(self, source: BeautifulSoup, id: str, label: str, title: str = "", content: str = ""):
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


def pre_process_html_tree(soup: BeautifulSoup):
    for script in soup(["script", "style"]):
        # remove all javascript and stylesheet code
        script.decompose()


def html_to_tree(parent: ArxivNode):
    if parent.get_id() == "root":
        title = parent.get_soup().find('h1', class_="ltx_title ltx_title_document", recursive=True)
        if title is None:
            raise Exception("Can't resolve title")
        title = title.text
        source = parent.get_soup().find('div', class_="ltx_abstract", recursive=True)
        content_wraper = source.find('p', class_='ltx_p')
        Abstract = ArxivNode(source, content_wraper.get('id'), "abstract", title, content_wraper.text)
        parent.add_child(Abstract)
        children = []
        for section in parent.get_soup().find_all('section', class_='ltx_section', recursive=True):
            print(f"section: {section['id']}")
            if not re.match(r'^S\d+$', section['id']):
                continue

            content = ""
            subsection = section.find('section', class_='ltx_subsection', recursive=False)
            if subsection:
                for e in subsection.previous_siblings:
                    if isinstance(e, Tag) and e.name == 'div' and 'ltx_para' in e.get('class', []):
                        content += e.get_text()
            else:
                content += section.get_text()

            Section = ArxivNode(section, section['id'], "section",
                                section.find_all_next('h2', class_="ltx_title ltx_title_section")[0].text, content)
            html_to_tree(Section)
            children.append(Section)
            print("----------")
        Abstract.set_children(children)
        Abstract._parent = parent

    elif parent.get_label() == "section":
        children = []
        for section in parent.get_soup().find_all('section', class_='ltx_subsection', recursive=False):
            if not re.match(r'^S\d+\.SS\d+$', section['id']):
                continue
            print(f"section: {section['id']}")
            # print(section)
            SubSection = ArxivNode(section, section['id'], "subsection",
                                section.find('h3', class_="ltx_title ltx_title_subsection").text, "")
            html_to_tree(SubSection)
            children.append(SubSection)

            print("----------")
        parent.set_children(children)
    elif parent.get_label() == "subsection":
        children = []
        for paragraph in parent.get_soup().find_all('div', class_='ltx_para', recursive=False):
            if not re.match(r'^S\d+\.SS\d+\.p.$', paragraph['id']):
                continue
            print(f"section: {paragraph['id']}")
            # print(section)
            Paragraph = ArxivNode(paragraph, paragraph['id'], "paragraph",
                                   "paragraph title", paragraph.text)
            children.append(Paragraph)

            print("----------")
        parent.set_children(children)
    return
    # sub_sections = section.find_all('section', class_='ltx_subsection', recursive=False)
    # if len(sub_sections) > 0:  # Case that need to handel subsections
    #     for sub_section in sub_sections:
    #         print(f"subsection: {sub_section['id']}")
    #         print(sub_section)
    #         print("----------")
    # else:  # Case that directly handel paragraph
    #     pass
    # print("\n\n\n\n\n")


html_srouce = requests.get("https://arxiv.org/html/2404.04326v1").text
soup = BeautifulSoup(html_srouce, "html.parser")
pre_process_html_tree(soup)

url = "https://arxiv.org/html/2404.04326v1"
soup = BeautifulSoup(html_srouce, "html.parser")
pre_process_html_tree(soup)

# This regex matches IDs that follow the pattern of any characters separated by dots
# regex for all section classes.

section_re = re.compile(r'^ltx.*section$')

elements = soup.find_all('section', class_=section_re)

for e in elements:
    print(e.get('id'))
    print(e.find_all(class_='ltx_title')[0].text)
head = ArxivNode(soup, "root", "root", "Title", "Content")
html_to_tree(head)
print(head)
head.display()