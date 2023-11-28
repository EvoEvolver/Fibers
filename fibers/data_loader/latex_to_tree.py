import re

from fibers.data_loader.bad_text_node_class import add_bad_reason
from fibers.tree import Tree, Node


def latex_to_tree(tex: str) -> Tree:
    tex = latex_to_markdown(tex)
    tree = latex_to_raw_tree(tex)
    divide_into_paragraphs(tree.root)
    return tree


def latex_to_raw_tree(tex: str):
    abstract = re.findall(r"\\begin{abstract}(.+?)\\end{abstract}", tex, re.DOTALL)[0].strip()
    title = re.findall(r"\\title{(.+?)}", tex, re.DOTALL)
    if len(title) > 0:
        title = title[0].strip()
        tex = re.sub(r"\\title{(.+?)}", r"", tex)
    else:
        title = ""
    tree = Tree()
    node = tree.root.s(title).be(tex)
    node.s("Abstract").be(abstract)
    for i in range(0, 4):
        process_section_level(i, 0, node)
    # delete the content before first section in the root
    # because it's usually irrelevant
    node.content = ""
    return tree


def latex_to_markdown(latex: str):
    # replace \textit{xxx} with *xxx*
    res = re.sub(r"\\textit{(.+?)}", r"*\1*", latex)
    # replace \textbf{xxx} with **xxx**
    res = re.sub(r"\\textbf{(.+?)}", r"**\1**", res)
    # remove \cite{xxx}
    res = re.sub(r"\\cite{.+?}", "[citations]", res)
    # replace \footnote{xxx} with (xxx)
    res = re.sub(r"\\footnote{(.+?)}", r"(\1)", res)
    # replace \item with -
    res = re.sub(r"\\item", "-", res)
    # remove \begin{enumerate} and \end{enumerate}
    res = re.sub(r"\\(begin|end){(enumerate|iterate)}", "\n", res)
    # remove \label{xxx}
    res = re.sub(r"\\label{.+?}", "", res)
    # remove lines starting with %
    res = re.sub(r"\n%.*", "", res)
    # replace more than two \n to two \n
    res = re.sub(r"\n{3,}", "\n\n", res)
    return res


def divide_text_into_section(section_level, tex):
    searched = r"((\\" + ("sub" * section_level) + "section)|paragraph)" + r"\*?{(.+?)}"
    # find first section
    m = re.search(searched, tex)
    if m:
        content = tex[:m.start()]
        tex = tex[m.start():]
    else:
        return tex, []
    sections = []
    for m in re.finditer(searched, tex):
        # get the section title
        section_title = m.group(3)
        # get the section content
        section_content = tex[m.end():]
        # find the end of the section content
        end = re.search(searched, section_content)
        if end:
            section_content = section_content[:end.start()]
        sections.append((section_title, section_content))

    return content, sections


def process_section_level(section_level, curr_level, node: Node):
    if section_level == curr_level:
        content, subsections = divide_text_into_section(section_level, node.content)
        node.content = content
        for subsection in subsections:
            node.s(subsection[0]).be(subsection[1].strip())
    else:
        for i, section in enumerate(node.children().values()):
            process_section_level(section_level, curr_level + 1, section)


def process_latex(latex: str):
    """
    Convert latex to markdown
    :param latex:
    :return:
    """

    # find \begin{abstract} and \end{abstract} and extract the text between
    abs = re.findall(r"\\begin{abstract}(.+?)\\end{abstract}", latex, re.DOTALL)

    # remove \begin{xxx}
    res = re.sub(r"\\begin{.+?}", "", latex)
    res = re.sub(r"\\end{.+?}", "", res)

    return res


def divide_into_paragraphs(node: Node):
    for child in node.children().values():
        divide_into_paragraphs(child)
    paragraphs = to_paragraphs(node.content)
    if len(paragraphs) == 0:
        return
    last_sibling = None
    for i, paragraph in enumerate(paragraphs):
        if last_sibling is None or len(last_sibling.content) + len(paragraph) > 1000:
            new_node = node.s(f"Segment {i + 1}").be(paragraph)
        else:
            new_node = last_sibling.be(last_sibling.content + " " + paragraph)
        add_bad_reason(node, "overlap_to_sibling")
        add_bad_reason(new_node, "bad_title")
        last_sibling = new_node
    node.content = ""

def to_paragraphs(text):
    # separate by \n\n
    paragraphs = text.split("\n\n")
    # remove empty paragraphs
    paragraphs = [p.strip() for p in paragraphs]
    paragraphs = [p for p in paragraphs if len(p) > 0]
    return paragraphs


if __name__ == "__main__":
    from fibers.testing.testing_trees import loader
    tex = loader.load_sample_src("scientific_understanding.tex")
    doc = latex_to_tree(tex)
    doc.show_tree_gui()
