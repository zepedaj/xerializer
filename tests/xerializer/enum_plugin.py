from xerializer import enum_plugin as mdl, Serializer
from unittest import TestCase
from enum import Enum


class MyEnum(Enum):
    a = 1
    b = 2


class TestEnumSerializer(TestCase):
    def test_all(self):

        mdl.register_enum(MyEnum)
        srlzr = Serializer()
        self.assertIs(MyEnum.a, srlzr.deserialize(srlzr.serialize(MyEnum.a)))
