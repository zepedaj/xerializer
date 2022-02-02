from xerializer.cli_tools import tree_builder as mdl

from unittest import TestCase


class TestAlphaConf(TestCase):

    def check_deps(self, node, expected_deps):
        # Check they match.
        self.assertEqual(
            actual_deps := set(id(x) for x in node.dependencies),
            set(id(x) for x in expected_deps))
        # Check they're unique.
        self.assertEqual(len(actual_deps), len(node.dependencies))

    def test_check_deps(self):

        ac = mdl.AlphaConf(
            ['abc',
             {'a': 2, 'b': '$3+1', 'c': "$'xyz'", 'd': [1, 2, "$r_('0')", "$r_[2]() + 3"]},
             2,
             {'e': '$2**3'}])

        ac.resolve()

        # Root
        self.check_deps(ac.node_tree, [ac[k] for k in range(4)])

        # List
        self.check_deps(ac[0], [])
        self.check_deps(ac[1], [ac[1][key].parent for key in 'abcd'])
        self.check_deps(ac[2], [])
        self.check_deps(ac[3], [ac[3]['e'].parent])

        # Dict keys
        for key_node in (
                [ac[1][key].parent for key in 'abcd'] +
                [ac[3]['e'].parent]):
            self.check_deps(key_node, [key_node.value])

        # Nested call dependecies
        self.check_deps(ac[1]['d'][2], [ac[0]])
        self.check_deps(ac[1]['d'][3], [ac[2]])
