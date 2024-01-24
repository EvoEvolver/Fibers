from fibers.tree import Node
from fibers.tree.node_class import NodeClass


class ImageNodeClass(NodeClass):
    pass


def set_image_by_path(node: Node, image_path: str):
    node.add_class(ImageNodeClass)
    with open(image_path, "rb") as f:
        image_data = f.read()
    ImageNodeClass.set_attr(node, "image", image_data)