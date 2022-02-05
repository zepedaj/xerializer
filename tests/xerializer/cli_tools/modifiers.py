from xerializer.cli_tools import modifiers as mdl
from xerializer.cli_tools.tree_builder import AlphaConf

from xerializer.cli_tools.dict_container import KeyNode
from xerializer.cli_tools.nodes import ParsedNode
from xerializer.cli_tools.ast_parser import Parser
from unittest import TestCase


class TestModifiers(TestCase):

    def test_parent(self):
        parser = Parser()
        key_node = KeyNode(
            'my_name',
            value_node := ParsedNode('$(n_, parent(n_))', parser=parser),
            parser=parser)
        self.assertEqual(resolved := key_node.resolve(), ('my_name', (value_node, key_node)))
        self.assertIs(resolved[1][0], value_node)
        self.assertIs(resolved[1][1], key_node)

    def test_hidden(self):

        for node, expected_resolved_value in [
                (AlphaConf([
                    0,
                    {'a': 1, 'b::hidden': 2, 'c': [3, 4]},
                    [5, {'d': 6, 'e': 7}, 8],
                ]).node_tree,
                    [
                    0,
                    {'a': 1, 'c': [3, 4]},
                    [5, {'d': 6, 'e': 7}, 8],
                ]),
        ]:

            self.assertTrue(node[1]['*b'].hidden)
            self.assertTrue(node[1]['b'].hidden)

            resolved_value = node.resolve()
            self.assertEqual(resolved_value, expected_resolved_value)
