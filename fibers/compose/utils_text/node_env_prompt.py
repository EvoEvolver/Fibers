import json

from fibers.tree import Node


def get_node_env_for_prompt(node: Node, before_prompt=""):
    children_list = []
    for key, child in node.children().items():
        children_list.append({
            "title": key,
            "content": child.content,
        })
    node_path = "\\".join(node.path())
    node_content = node.content
    prompt = f"""{before_prompt}"""
   # prompt += f"\nNode's path on the tree: {node_path}"
    if len(node_content) > 0:
        prompt += f"\nNode content: {node_content}\n"
    prompt += f"""Children: 
{json.dumps(children_list, indent=1)}
"""
    return prompt