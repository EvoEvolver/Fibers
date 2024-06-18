from fibers.tree import Node

if __name__ == '__main__':
    node = Node("root")
    child = node.new_child()
    child.title = "child"
    child.content = "<SendMessage send_message_to_main={send_message_to_main}/>"
    node.display(interactive=True)