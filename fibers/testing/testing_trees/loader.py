import json
import os

from fibers.data_loader.document import Document
from fibers.data_loader.html_to_tree import html_to_tree
from fibers.data_loader.markdown_to_tree import markdown_to_tree
from fibers.tree import Tree

curr_dir = os.path.dirname(os.path.abspath(__file__))

def load_sample_src(path: str) -> str:
    with open(os.path.join(curr_dir, path), "r") as f:
        src = f.read()
    return src

def load_sample_tree(path: str) -> Tree:
    ext_name = os.path.splitext(path)[1]
    src = load_sample_src(path)
    match ext_name:
        case ".json":
            src_dict = json.loads(src)
            tree = Document.from_dict(src_dict).to_tree()
        case ".md":
            file_name = os.path.splitext(path)[0]
            tree = markdown_to_tree(src, file_name)
        case ".html":
            tree = html_to_tree(src)
        case _:
            raise ValueError(f"Unknown file extension {ext_name}")
    return tree


if __name__ == "__main__":
    #tree0 = load_sample_tree("dingzhen_world.json")
    tree1 = load_sample_tree("Feyerabend.md")
    tree1.show_tree_gui()