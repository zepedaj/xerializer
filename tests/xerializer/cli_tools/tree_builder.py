from xerializer.cli_tools import tree_builder as mdl

from unittest import TestCase


class TestAlphaConf(TestCase):

    def test_build_node_tree(self):

        for raw_data, expected in [
                #
                (1, 1),
                #
                ([1, {'a': 2, 'b': '$3+1', 'c': "$'xyz'", 'd': [1, 2, '$"alpha"']},
                  2, {'e': '$2**3'}],
                 [1, {'a': 2, 'b': 4, 'c': 'xyz', 'd': [1, 2, 'alpha']},
                  2, {'e': 8}]),
                #
                (['abc', {'a': 2, 'b': '$3+1', 'c': "$'xyz'", 'd': [1, 2, "$r_('0')", "$r_[0]() + 'x'"]},
                  2, {'e': '$2**3'}],
                 ['abc', {'a': 2, 'b': 4, 'c': 'xyz', 'd': [1, 2, 'abc', 'abcx']},
                  2, {'e': 8}]),
        ]:
            self.assertEqual(
                resolved := (ac_obj := mdl.AlphaConf(raw_data)).resolve(),
                expected)
            self.assertIs(type(resolved), type(expected))

    def test_resolve_root(self):

        raw_data = [1, {'a': 2, 'b': '$3+1', 'c': "$'xyz'", 'd': [1, 2, '$r_']},
                    2, {'e': '$2**3'}]
        aconf = mdl.AlphaConf(raw_data)
        self.assertIs(
            aconf.node_tree, aconf.resolve()[1]['d'][2])
