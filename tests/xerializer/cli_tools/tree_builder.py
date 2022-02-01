from xerializer.cli_tools import tree_builder as mdl

from unittest import TestCase


class TestAlphaConf(TestCase):

    def test_build_node_tree(self):

        for raw_data, expected in [
                (1, 1),
                ([1, {'a': 2, 'b': '$3+1', 'c': "$'xyz'", 'd': [1, 2, '$"alpha"']},
                  2, {'e': '$2**3'}],
                 [1, {'a': 2, 'b': 4, 'c': 'xyz', 'd': [1, 2, 'alpha']},
                  2, {'e': 8}]),
        ]:
            self.assertEqual(
                resolved := mdl.AlphaConf(raw_data).resolve(),
                expected)
            self.assertIs(type(resolved), type(expected))
