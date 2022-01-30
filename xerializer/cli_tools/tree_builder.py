from .containers import DictContainer, ListContainer
from .nodes import KeyNode, ValueNode


def _as_node_tree(raw_data, parser, parent=None):
    """
    Recursively converts the input raw_data into a node tree. Lists and dictionaries in the tree
    will result in nested levels.
    """

    if isinstance(raw_data, dict):
        # Create a dictionary container.
        out = DictContainer(
            parent=parent, parser=parser)
        for key, val in raw_data.items():
            key_node = KeyNode(
                key, parser=parser, content=_as_node_tree(val, parser))
            out.add(key_node)  # Sets parent.

    elif isinstance(raw_data, list):
        # Create a list container.
        out = ListContainer(
            parent=parent, parser=parser)
        for val in raw_data:
            out.add(_as_node_tree(val, parser=parser))  # Sets parent.

    else:
        # Create a value container.
        return ValueNode(
            raw_data, parser=parser, parent=parent)


class ConfTree:
    def __init__(self, data, parser):
        parser.register({'root': self})
        self.node_tree = _as_node_tree(data)
