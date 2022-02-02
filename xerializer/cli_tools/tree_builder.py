

from .containers import ListContainer
from .dict_container import DictContainer, KeyNode
from .nodes import ValueNode
from .ast_parser import Parser


class AlphaConf:

    def __init__(self, raw_data, context: dict = {}, parser=None):
        """
        :param raw_data: The data to convert to an :class:`AlphaConf` object.
        :param context: Extra parameters to add to the parser context.
        :param parser: The parser to use (instantiated internally by default).
        """
        self.parser = parser or Parser(context)
        self.node_tree = self.build_node_tree(raw_data, parser=self.parser)
        # self.node_tree.modify() # Apply modifiers.
        self.parser.register('r_', self.node_tree)

    @classmethod
    def build_node_tree(cls, raw_data, parser, parent=None):
        """
        Recursively converts the input raw_data into a node tree. Lists and dictionaries in the tree
        will result in nested levels.
        """

        #
        if isinstance(raw_data, dict):
            # Create a dictionary container.
            out = DictContainer()
            for key, val in raw_data.items():
                key_node = KeyNode(
                    key, cls.build_node_tree(val, parser), parser=parser)
                out.add(key_node)  # Sets parent.

        elif isinstance(raw_data, list):
            # Create a list container.
            out = ListContainer()
            for val in raw_data:
                out.add(cls.build_node_tree(val, parser))  # Sets parent.

        else:
            # Create a value container.
            out = ValueNode(
                raw_data, parser=parser)

        #
        return out

    def resolve(self):
        return self.node_tree.resolve()
