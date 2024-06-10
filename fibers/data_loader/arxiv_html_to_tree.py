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
        content = ""
        subsection = section.find('section', class_='ltx_subsection', recursive=False)
        if subsection:  # if there are subsection, try to find leading paragraph before the first subsection to set them as the content of the section
            for e in subsection.previous_siblings:
                if isinstance(e, Tag) and e.name == 'div' and 'ltx_para' in e.get('class', []):
                    content += e.get_text()
        # else:  # if there are no subsection, the content of the section is directly set.
        #     content += section.get_text()

        Section = ArxivNode(section, section['id'], "section",
                            section.find_all_next('h2', class_="ltx_title ltx_title_section")[0].text, content)
        html_to_tree(Section)
        children.append(Section)
        print("----------")
    return children


def get_subsection_nodes(sectionSoup: BeautifulSoup) -> list[ArxivNode]:
    children = []
    for section in sectionSoup.find_all('section', class_='ltx_subsection', recursive=False):
        if not re.match(r'^S\d+\.SS\d+$', section['id']):
            continue
        print(f"section: {section['id']}")
        # print(section)
        SubSection = ArxivNode(section, section['id'], "subsection",
                               section.find('h3', class_="ltx_title ltx_title_subsection").text, "")
        html_to_tree(SubSection)
        children.append(SubSection)

        print("----------")
    return children

def get_paragraph_nodes(subsectionSoup: BeautifulSoup) -> list[ArxivNode]:
    children = []
    index = 1
    for paragraph in subsectionSoup.find_all('div', class_='ltx_para', recursive=False):
        if not re.match(r'^S\d+\.SS\d+\.p.$', paragraph['id']):
            continue
        print(f"section: {paragraph['id']}")
        # print(section)
        Paragraph = ArxivNode(paragraph, paragraph['id'], "paragraph",
                              "paragraph " + str(index), '<!DOCTYPE html><meta content=\"text/html; charset=utf-8\" http-equiv=\"content-type\"/>'+paragraph.__str__())
        children.append(Paragraph)
        index += 1

        print("----------")
    return children


def html_to_tree(parent: ArxivNode):
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
            # TODO: Need fix visualization, for some special character, the web can't render correctly, will cause the whole content be blank
            parent.content = re.sub(r'[^\w@._\,\(\)\n&\{\} ]+', '', author.text)

        Abstract = get_abstract_node(parent.get_soup())
        parent.add_child(Abstract)
        Abstract.set_children(get_section_nodes(parent.get_soup()))

    elif parent.get_label() == "section":
        parent.set_children(get_subsection_nodes(parent.get_soup()))
    elif parent.get_label() == "subsection":
        parent.set_children(get_paragraph_nodes(parent.get_soup()))
    return


if __name__ == '__main__':
    # html_source = requests.get("https://arxiv.org/html/2404.04326v1").text
    # with open("cached_page.html", "w", encoding="utf-8") as f:
    #     f.write(html_source)
    try:
        with open("cached_page.html", "r", encoding="utf-8") as f:
            html_source = f.read()
    except FileNotFoundError:
        print("Error: Cached HTML file not found.")
    soup = BeautifulSoup(html_source, "html.parser")
    pre_process_html_tree(soup)
    head = ArxivNode(soup, "root", "root", "", "")
    html_to_tree(head)
    head.display()

    # # This regex matches IDs that follow the pattern of any characters separated by dots
    # # regex for all section classes.
    #
    # section_re = re.compile(r'^ltx.*section$')
    #
    # elements = soup.find_all('section', class_=section_re)
    #
    # for e in elements:
    #     print(e.get('id'))
    #     print(e.find_all(class_='ltx_title')[0].text)
