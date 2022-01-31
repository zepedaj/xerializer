from xerializer.cli_tools import nodes as mdl
from xerializer.cli_tools.ast_parser import Parser

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
