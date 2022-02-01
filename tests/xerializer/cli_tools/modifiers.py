from xerializer.cli_tools import modifiers as mdl

from xerializer.cli_tools.dict_container import KeyNode
from xerializer.cli_tools.nodes import ValueNode
from xerializer.cli_tools.ast_parser import Parser
from unittest import TestCase


class TestModifiers(TestCase):

    def test_parent(self):
        parser = Parser()
        key_node = KeyNode(
            'my_name',
            value_node := ValueNode('$(n_, parent(n_))', parser=parser),
            parser=parser)
        self.assertEqual(resolved := key_node.resolve(), ('my_name', (value_node, key_node)))
        self.assertIs(resolved[1][0], value_node)
        self.assertIs(resolved[1][1], key_node)
