from xerializer import builtin_plugins as mdl, Serializer
from unittest import TestCase
from abc import ABC, ABCMeta


class MyABCClass(ABC):
    pass


class TestBuiltinPlugins(TestCase):
    # The main functionality is currently tested in serializer.py

    def test_signatures(self):

        # TypeSerializers
        some_expected = ['set', 'slice', 'tuple', 'dict']
        processed = []
        for srlzr_type in vars(mdl).values():
            if (
                    isinstance(srlzr_type, type) and
                    issubclass(srlzr_type, mdl._BuiltinTypeSerializer) and
                    not srlzr_type == mdl._BuiltinTypeSerializer):
                srlzr = srlzr_type()
                if srlzr.handled_type not in [ABCMeta, type]:
                    self.assertEqual(srlzr.signature, srlzr.handled_type.__name__)
                processed.append(srlzr.signature)

        self.assertEqual(len(set(some_expected) - set(processed)), 0)

        # Serializables
        self.assertEqual(mdl.Literal.get_signature(), 'Literal')

    def test_serialization(self):
        serializer = Serializer()

        for _obj in [
                MyABCClass, dict,
                b'abcdef',
        ]:
            srlzd_obj = serializer.serialize(_obj)
            self.assertIsInstance(srlzd_obj, str)
            self.assertEqual(_obj, serializer.deserialize(srlzd_obj))

    def test_dict_serialization(self):
        serializer = Serializer()

        with self.assertRaisesRegex(ValueError, 'Invalid keys .*garbage.*'):
            serializer.from_serializable({'__type__': 'dict', 'value': {1: 2}, 'garbage': 1})

        self.assertEqual(
            serializer.from_serializable({'__type__': 'dict', 'value': {1: 2}}),
            {1: 2})

        self.assertEqual(
            serializer.from_serializable({'__type__': 'dict', 'value': [[1, 2]]}),
            {1: 2})

        self.assertEqual(
            serializer.from_serializable({'__type__': 'dict'}),
            {})
