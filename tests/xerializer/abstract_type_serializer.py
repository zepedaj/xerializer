from xerializer import abstract_type_serializer as mdl
from xerializer import _registered
from unittest import TestCase
from xerializer.serializer import Serializer
from xerializer import create_signature_aliases
import re


def _as_registered():
    return [type(_x) for _x in _registered._THIRD_PARTY_PLUGINS if _x.as_serializable]


def _from_registered():
    return [type(_x) for _x in _registered._THIRD_PARTY_PLUGINS if _x.from_serializable]


class TestRegistration(TestCase):
    def test_TypeSerializer_registration(self):
        _registered._THIRD_PARTY_PLUGINS.clear()

        # Abstract derived class.
        class MyAbstractTypeSerializer(mdl.TypeSerializer):
            pass

        self.assertEqual(_as_registered(), [])
        self.assertEqual(_from_registered(), [])

        #
        with self.assertRaisesRegex(
            Exception,
            re.escape(
                "Cannot register abstract class <class 'tests.xerializer.abstract_type_serializer"
                ".TestRegistration.test_TypeSerializer_registration.<locals>."
                "MyFailsedAbstractTypeSerializer'>."
            ),
        ):
            # containing the following abstract methods: "
            # "['as_serializable', 'handled_type'].")):
            class MyFailsedAbstractTypeSerializer(
                mdl.TypeSerializer, register_meta=True
            ):
                pass

        # Non-abstract double-derived class.
        class MyGrandChildTypeSerializer(mdl.TypeSerializer):
            handled_type = str

            def as_serializable(self):
                pass

        self.assertEqual(_as_registered(), _as_list := [MyGrandChildTypeSerializer])
        self.assertEqual(_from_registered(), _from_list := [MyGrandChildTypeSerializer])

        # De-serialization only derived class.
        class MyTypeSerializer(mdl.TypeSerializer):
            signature = "my_type"
            handled_type = str

            as_serializable = None
            aliases = ["alias1", "alias2"]

        create_signature_aliases(MyTypeSerializer().signature, ["alias3", "alias4"])

        self.assertEqual(_as_registered(), _as_list)
        self.assertEqual(
            _from_registered(), _from_list := (_from_list + [MyTypeSerializer])
        )

        # Non-registered derived class
        class MyTypeSerializerChild1(MyTypeSerializer):
            register = False

            def as_serializable(self):
                pass

        class MyTypeSerializerChild2(MyTypeSerializerChild1):
            register = True
            pass

        class MyTypeSerializerChild3(MyTypeSerializerChild1, register_meta=False):
            register = True
            pass

        class MyTypeSerializerChild4(MyTypeSerializerChild1, register_meta=True):
            register = False
            pass

        self.assertEqual(
            _as_registered(),
            _as_list := (_as_list + [MyTypeSerializerChild2, MyTypeSerializerChild4]),
        )
        self.assertEqual(
            _from_registered(),
            _from_list := (
                _from_list + [MyTypeSerializerChild2, MyTypeSerializerChild4]
            ),
        )

        # Test signature aliases
        srlzr = Serializer()
        for signature in [
            MyTypeSerializer().signature,
            "alias1",
            "alias2",
            "alias3",
            "alias4",
        ]:
            self.assertIsInstance(
                srlzr.from_serializable({"__type__": signature}),
                MyTypeSerializer.handled_type,
            )
