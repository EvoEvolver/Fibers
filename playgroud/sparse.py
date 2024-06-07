import inspect
import os

import fibers
from fibers.tree.node_attr.code_node import get_obj
from fibers.data_loader.module_to_tree import get_tree_for_module
from fibers.tree.node import Node
from mllm import Chat, debug, caching
import re

import test_sparse


def get_comments(source_code):
    prev = None
    content_lines = []
    start = False
    for s in source_code.split("\n"):
        if start:
            content_lines.append(s)
            if '\"\"\"' in s:
                break
        elif '\"\"\"' in s and prev and ("def" in prev or "class" in prev):
            content_lines.append(s)
            start = True
        prev = s
    return "\n".join(content_lines)


def remove_comments(source_code):
    in_multiline_string = False
    non_comment_lines = []
    for line in source_code.split("\n"):
        stripped_line = line.strip()
        if '"""' in stripped_line or "'''" in stripped_line:
            if in_multiline_string:
                in_multiline_string = not in_multiline_string
                continue
            else:
                quote_count = stripped_line.count('"""') + stripped_line.count("'''")
                if quote_count >= 2:
                    if quote_count == 2 and not in_multiline_string:
                        non_comment_lines.append(line)
                    continue
                else:
                    in_multiline_string = not in_multiline_string
                    continue
        if in_multiline_string:
            continue
        non_comment_lines.append(line)
    return "\n".join(non_comment_lines)


def summarize_content(node: Node):
    chat = Chat()
    prompt = f"""
                                           Given a parent node named "{node.title}" with content "{node.content}"(could be empty), please summary this node in two sentence according to its childrens information and return the result in JSON format, with tag summary:
                                           """
    for i, child in enumerate(node.children()):
        source = child.src()
        if len(child.children()) == 0:
            content, method_def = source_optimize(source)
            prompt += f"""
                                       <node>
                                       content:
                                       {content}
                                       source code:
                                       {method_def}
                                       </node>
                                       """
        else:
            prompt += f"""
                                                 <node>
                                                 content:
                                                 {child.content}
                                                 </node>
                                                 """
    chat += prompt
    print(f"prompt:{prompt}")
    res = chat.complete(parse="dict", cache=True, expensive=True)
    print(f"result:{res}")
    return res["summary"]


def source_optimize(source_code: str):
    if len(source_code) > 700:  # Compress when source code is long
        chat = Chat()
        prompt = f"""I will send you the source code of a function, please consider the source code and its comment, give a one to two sentence summary about the function, return as JSON format with tag 'summary'. Anso, keep the function signature of the function, return with tag 'signature':
        <source>
            {source_code}
        </srouce>
        """
        chat += prompt
        res = chat.complete(parse="dict", cache=True, expensive=True)
        print(f"result:{res}")
        return res["summary"], str(res["signature"]) + "\n..."
    else:
        return get_comments(source_code), remove_comments(source_code)


if __name__ == '__main__':


    chat = Chat()

    tree = get_tree_for_module(test_sparse)

    bfs_reverse = [n for n in tree.iter_subtree_with_bfs()]
    bfs_reverse.reverse()
    for node in bfs_reverse:
        if len(node.title) > 0:
            children = node.children()
            child_num = len(children)

            if child_num > 7:
                prompt = f"""
                                Given a parent node named "{node.title}", categorize its child nodes into no more than 5 distinct groups based on their content, and better make each group have average number of members. Assign a descriptive name to each category, reflecting the collective meaning or theme of the nodes it contains.
    
                                Please format the response as JSON, which should include a 'categories' field listing all category names, and additional fields for each category name. Under each category name, include the IDs of the nodes belonging to that category.
    
                                Node details are as follows:
                                """

                for i, child in enumerate(node.children()):
                    source = child.src()
                    if len(child.children()) == 0:
                        content, method_def = source_optimize(source)
                        prompt += f"""
                                                               <node>
                                                               id={i}
                                                               content:
                                                               {content}
                                                               source code:
                                                               {method_def}
                                                               </node>
                                                               """
                    else:
                        prompt += f"""
                                                                         <node>
                                                                         id={i}
                                                                         content:
                                                                         {child.content}
                                                                         </node>
                                                                         """
                chat += prompt
                print(prompt)
                res = chat.complete(parse="dict", cache=True, expensive=True)

                print(f"result:{res}")

                node.set_children([Node(res["categories"][i], "") for i in range(len(res["categories"]))])
                for child in node.children():
                    if child.title in res:
                        print([i for i in res[child.title]])
                        child.set_children([children[i] for i in res[child.title]])
                    child.content = summarize_content(child)
            elif child_num > 0:
                node.content = summarize_content(node)

    head = bfs_reverse[-1]
    print(bfs_reverse[-1])
    tree.display()
