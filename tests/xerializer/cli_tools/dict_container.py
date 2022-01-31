from xerializer.cli_tools import dict_container as mdl

import re
from unittest import TestCase
from pglib.py import setdefaultattr
from xerializer.cli_tools.ast_parser import Parser
from xerializer.cli_tools.nodes import ValueNode

# Test modifiers


def add_val_modif(key, val):
    def wrapper(node):
        modifs = setdefaultattr(node, 'modifs', {})
        modifs[key] = val
    return wrapper

# Test classes


class TestRawKeyPatterns(TestCase):
    def test_parse_raw_key(self):
        for raw_key, expected in [
            ('my_key',
             {'name': 'my_key',
              'types': None,
              'modifiers': None}),
            ('my_key:int',
             {'name': 'my_key',
              'types': 'int',
              'modifiers': None}),
            ('my_key:"my.xerializer:Type"',
             {'name': 'my_key',
              'types': '"my.xerializer:Type"',
              'modifiers': None}),
            ('my_key::modif1,modif2(1,2),modif3',
             {'name': 'my_key',
              'types': None,
              'modifiers': 'modif1,modif2(1,2),modif3'}),
            ('my_key:int:modif1,modif2,modif3(64,"abc",True)',
             {'name': 'my_key',
              'types': 'int', 'modifiers':
              'modif1,modif2,modif3(64,"abc",True)'}),
            ('my_key:"my.xerializer:Type":modif1,modif2,modif3(64,"abc",True)',
             {'name': 'my_key',
              'types': '"my.xerializer:Type"',
              'modifiers': 'modif1,modif2,modif3(64,"abc",True)'}),
            ('my_key:(str,"my.xerializer:Type",float,int):modif1,modif2,modif3(64,"abc",True)',
             {'name': 'my_key',
              'types': '(str,"my.xerializer:Type",float,int)',
              'modifiers': 'modif1,modif2,modif3(64,"abc",True)'}),
        ]:
            self.assertEqual(
                mdl.KeyNode._parse_raw_key(raw_key), expected)


class TestKeyNode(TestCase):
    @classmethod
    def get_node(cls, name='my_key'):
        parser = Parser({'add_val': add_val_modif})
        node = mdl.KeyNode(
            f'{name}:"my.xerializer:Type":add_val(0, "abc"),add_val(1,2),add_val(2,True)',
            ValueNode('$10+1', parser),
            parser=parser)
        return node

    def test_all(self):

        node = self.get_node()

        # Check modifications
        self.assertEqual(node.modifs[0], 'abc')
        self.assertEqual(node.modifs[1], 2)
        self.assertEqual(node.modifs[2], True)

        #
        self.assertEqual(node.resolve(), ('my_key', 11))


class TestDictContainer(TestCase):

    def test_hashing(self):
        node1 = TestKeyNode.get_node()
        node2 = TestKeyNode.get_node()
        node3 = TestKeyNode.get_node('my_key_3')

        container = mdl.DictContainer()
        container.add(node1)
        container.add(node2)
        container.add(node3)

        self.assertEqual(len(container.children), 2)
        # Both hashes match, so retreiven node1 or node2
        # should result in the same node.
        self.assertIs(container.children[node1], node2)

    def test_rename_key(self):
        node1 = TestKeyNode.get_node()
        node2 = TestKeyNode.get_node()

        container = mdl.DictContainer()
        [container.add(x) for x in [node1, node2]]

        # Test parent relationships.
        self.assertIs(node1.parent, None)
        self.assertIs(node2.parent, container)

        # Test renaming bound KeyNode
        node1.name = 'abc'  # Works, as node1 was removed when adding node2.
        with self.assertRaisesRegex(
                Exception,
                re.escape(f'Remove `{node2}` from parent container before re-naming.')):
            node2.name = 'abc'

        # Test removal
        self.assertEqual(
            {'my_key'}, set(container.children.keys()))
        container.remove(node2)
        self.assertEqual(
            set(), set(container.children.keys()))
