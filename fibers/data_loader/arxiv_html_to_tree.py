import base64
import html
import os
import re
from typing import List

import html2text
import requests
from bs4 import BeautifulSoup, PageElement

from fibers.data_loader.bad_text_node_class import add_bad_reason
from fibers.tree import Node
from fibers.tree.node_attr import Attr


def pre_process_html_tree(soup: BeautifulSoup):
    for script in soup(["script", "style"]):
        # remove all javascript and stylesheet code
        script.decompose()


html = requests.get("https://arxiv.org/html/2404.04326v1").text
soup = BeautifulSoup(html, "html.parser")
pre_process_html_tree(soup)

url = "https://arxiv.org/html/2404.04326v1"
soup = BeautifulSoup(html, "html.parser")
pre_process_html_tree(soup)

# This regex matches IDs that follow the pattern of any characters separated by dots
# regex for all section classes.

section_re = re.compile(r'^ltx.*section$')

elements = soup.find_all('section', class_=section_re)

for e in elements:
    print(e.get('id'))
    print(e.find_all(class_ = 'ltx_title')[0].text)