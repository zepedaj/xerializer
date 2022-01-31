from xerializer.cli_tools import dict_container as mdl

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

    def test_all(self):

        parser = Parser({'add_val': add_val_modif})
        node = mdl.KeyNode(
            'my_key:"my.xerializer:Type":add_val(0, "abc"),add_val(1,2),add_val(2,True)',
            ValueNode('$10+1', parser),
            parser=parser)

        # Check modifications
        self.assertEqual(node.modifs[0], 'abc')
        self.assertEqual(node.modifs[1], 2)
        self.assertEqual(node.modifs[2], True)

        #
        self.assertEqual(node.resolve(), ('my_key', 11))
