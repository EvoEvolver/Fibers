from __future__ import annotations

from typing import List, Callable

from mllm.utils import parallel_map

from fibers.tree import Node


def node_map_with_dependency(nodes_to_map: List[Node], mapping_func: Callable[[Node], bool], n_workers=8) -> None:
    """
    Apply a mapping function to nodes. The mapping function might fail if the node depends on other nodes that have not been mapped yet.
    This function will keep trying to map the nodes until all nodes are mapped.
    """
    if not isinstance(nodes_to_map, list):
        nodes_to_map = list(nodes_to_map)
    while len(nodes_to_map) > 0:
        indices_to_remove = []
        has_new_finished = False
        for i, finished in parallel_map(mapping_func, nodes_to_map, n_workers=n_workers, title="summary"):
            if finished:
                indices_to_remove.append(i)
                has_new_finished = True
        if not has_new_finished:
            print("some node is not mapped")
            break
        for i in indices_to_remove[::-1]:
            nodes_to_map.pop(i)


class NodeMap:
    def __init__(self, content_map=None, title_map=None):
        self._content_map: Callable[
            [Node], str] = content_map if content_map is not None else lambda x: x.content
        self._title_map: Callable[
            [Node], str] = title_map if title_map is not None else lambda x: x.title

    def get_title_and_content(self, node: Node):
        """
        Usage: title, content = content_map.get_title_and_content(node)
        """
        return self._title_map(node), self._content_map(node)


default_map = NodeMap()
