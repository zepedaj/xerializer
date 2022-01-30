from xerializer.cli_tools import node as mdl

from unittest import TestCase


class TestKeyNode(TestCase):
    def test_parse_raw_key(self):
        for raw_key, expected in [
            ('my_key',
             {'name': 'my_key',
              'type': None,
              'modifiers': None}),
            ('my_key:int',
             {'name': 'my_key',
              'type': 'int',
              'modifiers': None}),
            ('my_key:"my.xerializer:Type"',
             {'name': 'my_key',
              'type': 'my.xerializer:Type',
              'modifiers': None}),
            ('my_key::modif1,modif2(1,2),modif3',
             {'name': 'my_key',
              'type': None,
              'modifiers': 'modif1,modif2(1,2),modif3'}),
            ('my_key:int:modif1,modif2,modif3(64,"abc",True)',
             {'name': 'my_key',
              'type': 'int', 'modifiers':
              'modif1,modif2,modif3(64,"abc",True)'}),
            ('my_key:"my.xerializer:Type":modif1,modif2,modif3(64,"abc",True)',
             {'name': 'my_key',
              'type': 'my.xerializer:Type',
              'modifiers': 'modif1,modif2,modif3(64,"abc",True)'}),
            ('my_key:(str,"my.xerializer:Type",float,int):modif1,modif2,modif3(64,"abc",True)',
             {'name': 'my_key',
              'type': '(str,"my.xerializer:Type",float,int)',
              'modifiers': 'modif1,modif2,modif3(64,"abc",True)'}),
        ]:
            self.assertEqual(
                mdl.KeyNode._parse_raw_key(raw_key), expected)
