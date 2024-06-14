

# Usage of `Attr`


`Attr` is a class that represents an attribute of a node. It is used to store data that is attached to the node, such as the python object that the node represents, or the summary of the subtree on the node. 

## Design motivation

Instead of using class inheritance to add attributes to a node, we use `Attr` to store the attributes of a node. This is because the attributes of a node are not part of the node itself, but rather additional information that is attached to the node.

- For each subclass of `Attr`, we can add one instance of the subclass to a node.
- To add `Attr` to a node (say `XXXAttr`): `attr = XXXAttr(node)`
- To get the attribute of a node: `attr = XXXAttr.get(node)`