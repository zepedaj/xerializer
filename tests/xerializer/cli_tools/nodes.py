from xerializer.cli_tools import nodes as mdl
from xerializer.cli_tools.nodes import ParsedNode
from xerializer.cli_tools.dict_container import KeyNode, DictContainer
from xerializer.cli_tools.containers import ListContainer
from xerializer.cli_tools.ast_parser import Parser
from xerializer.cli_tools.tree_builder import AlphaConf

from unittest import TestCase


class TestParsedNode(TestCase):

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

            node = mdl.ParsedNode(raw_value=raw_value, parser=Parser())
            #
            self.assertEqual(resolved_value := node.resolve(), expected_resolved_value)
            self.assertIs(type(resolved_value), type(expected_resolved_value))

    def test_current_node_resolution(self):
        parser = Parser()

        #
        node = KeyNode('my_name', value_node := mdl.ParsedNode('$n_', parser=parser), parser=parser)
        self.assertEqual(resolved := node.resolve(), ('my_name', value_node))
        self.assertIs(resolved[1], value_node)

    def test_call(self):
        parser = Parser()

        #
        node = KeyNode('my_name', value_node := mdl.ParsedNode('$n_', parser=parser), parser=parser)
        self.assertEqual(node(), ('my_name', value_node))

    def test_qual_name(self):

        #
        ac = AlphaConf({'node0': {'node1': 1}})

        for root, ref_str__exp_node__exp_type__exp_value in [
            # Dict-of-dict
            (_root := AlphaConf(
                _raw_data := {'node0': {'node1': 1}}).node_tree,
             [
                 ('', _root, DictContainer,
                  _raw_data),
                 ('node0', _root.children['node0'].value, DictContainer,
                  _raw_data['node0']),
                 ('*node0', _root.children['node0'], KeyNode,
                  ('node0', _raw_data['node0'])),
                 ('node0.node1', _root.children['node0'].value.children['node1'].value,
                  ParsedNode, _raw_data['node0']['node1']),
            ]),
            # ParsedNode
            (_root := ParsedNode('abc', None),
             [
                 ('', _root, ParsedNode, 'abc'),
            ]),
            # List
            (_root := AlphaConf(
                _raw_data := [0, {'a': 1, 'b': 2, 'c': [3, 4]}, [5, {'d': 6, 'e': 7}, 8], ]).node_tree,
             [
                 ('', _root, ListContainer, _raw_data),
                 ('0', _root.children[0], ParsedNode, _raw_data[0]),
                 ('1.c.1', _root[1]['c'][1], ParsedNode, _raw_data[1]['c'][1]),
                 ('1.*c', _root[1]['*c'], KeyNode, ('c', _raw_data[1]['c'])),
                 ('2.1.e', _root.children[2][1]['e'], ParsedNode, _raw_data[2][1]['e']),
            ]),
        ]:
            for ref, expected_node, expected_type, expected_value in \
                    ref_str__exp_node__exp_type__exp_value:
                #
                actual_node = root.node_from_ref(ref)
                assert type(expected_node) is expected_type
                assert type(actual_node) is expected_type
                assert actual_node is expected_node
                assert actual_node.qual_name == ref
                assert actual_node() == expected_value

    def test_node_from_ref(self):
        #
        for root, ref__expected_node__tuples in [
            (r_ :=
             AlphaConf(
                 _raw_data := [
                     0,
                     {'a': 1, 'b': 2, 'c': [3, 4]},
                     [5, {'d': 6, 'e': 7}, 8],
                 ]).node_tree,
             [
                 (r_.node_from_ref('1.b..c'),
                  r_[1]['c']),
                 #
                 (r_[1]['c'].node_from_ref('...2.1.d'),
                  r_[2][1]['d'])]
             )]:

            for node_from_ref, expected_node in ref__expected_node__tuples:
                self.assertIs(node_from_ref, expected_node)
