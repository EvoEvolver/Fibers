from fibers.helper.utils import RobustParse
from fibers.model.chat import Chat
from fibers.transform.utils_text.node_env_prompt import get_node_env_for_prompt
from fibers.tree import Node, Tree




if __name__ == "__main__":
    tree = Tree()
    root = tree.root
    root.s("a").be("a")
    root.s("c").be("c")
    print(children_summarize(*get_node_env_for_prompt(root)))