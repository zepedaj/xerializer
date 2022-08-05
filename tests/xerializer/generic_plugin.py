from xerializer import generic_plugin as mdl
from xerializer import Serializer
from unittest import TestCase


class MyClass:
    a = 1

    def __init__(self, b):
        self.b = b


class TestGeneric(TestCase):
    def test_all(self):
        mc = MyClass(b=3)

        # No class var
        mdl.register_generic(MyClass)
        srlzr = Serializer()
        dmc = srlzr.deserialize(srlzr.serialize(mc))
        with self.assertRaises(AttributeError):
            dmc.a
        [self.assertEqual(getattr(mc, key), getattr(dmc, key)) for key in ["b"]]

        # With 'only' a
        mdl.register_generic(MyClass, only=["a"])
        srlzr = Serializer()
        dmc = srlzr.deserialize(srlzr.serialize(mc))
        with self.assertRaises(AttributeError):
            dmc.b
        [self.assertEqual(getattr(mc, key), getattr(dmc, key)) for key in ["a"]]
        self.assertIs(dmc.source_class, MyClass)

        # With 'include' a
        mdl.register_generic(MyClass, include=["a"])
        srlzr = Serializer()
        dmc = srlzr.deserialize(srlzr.serialize(mc))
        [self.assertEqual(getattr(mc, key), getattr(dmc, key)) for key in ["a", "b"]]
        self.assertIs(dmc.source_class, MyClass)

        # With 'exclude' b
        mdl.register_generic(MyClass, exclude=["b"])
        srlzr = Serializer()
        dmc = srlzr.deserialize(srlzr.serialize(mc))
        with self.assertRaises(AttributeError):
            dmc.a
        with self.assertRaises(AttributeError):
            dmc.b
        self.assertIs(dmc.source_class, MyClass)
