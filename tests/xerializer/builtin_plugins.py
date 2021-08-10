from xerializer import builtin_plugins as mdl, Serializer
from unittest import TestCase


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
                self.assertEqual(srlzr.signature, srlzr.handled_type.__name__)
                processed.append(srlzr.signature)

        self.assertEqual(len(set(some_expected) - set(processed)), 0)

        # Serializables
        self.assertEqual(mdl.Literal.get_signature(), 'Literal')

    def test_serialization(self):
        serializer = Serializer()

        for _obj in [
                b'abcdef'
        ]:
            srlzd_obj = serializer.serialize(_obj)
            self.assertIsInstance(srlzd_obj, str)
            self.assertEqual(_obj, serializer.deserialize(srlzd_obj))
