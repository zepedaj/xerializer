from xerializer.cli_tools import nodes as mdl
from xerializer.cli_tools.dict_container import KeyNode
from xerializer.cli_tools.ast_parser import Parser
from xerializer.cli_tools.tree_builder import AlphaConf

from unittest import TestCase


class TestValueNode(TestCase):

    def test_resolve(self):
        for raw_value, expected_resolved_value in [
                #
                (r"\'abc'", r"'abc'"),
                #
                (1, 1),
                (1.234e-6, 1.234e-6),
                (True, True),
                #
                ("$True", True),
                ("$(1+3)/4", (1+3)/4),
        ]:

            node = mdl.ValueNode(raw_value=raw_value, parser=Parser())
            #
            self.assertEqual(resolved_value := node.resolve(), expected_resolved_value)
            self.assertIs(type(resolved_value), type(expected_resolved_value))

    def test_current_node_resolution(self):
        parser = Parser()

        #
        node = KeyNode('my_name', value_node := mdl.ValueNode('$n_', parser=parser), parser=parser)
        self.assertEqual(resolved := node.resolve(), ('my_name', value_node))
        self.assertIs(resolved[1], value_node)

    def test_call(self):
        parser = Parser()

        #
        node = KeyNode('my_name', value_node := mdl.ValueNode('$n_', parser=parser), parser=parser)
        self.assertEqual(node(), ('my_name', value_node))
