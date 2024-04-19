from dataclasses import dataclass
from unittest import TestCase
import datetime
from jztools.py import strict_zip
import pytz
from xerializer import builtin_plugins
from xerializer.builtin_plugins import Literal
from json import JSONDecodeError
from tempfile import NamedTemporaryFile
from xerializer import serializer as mdl
from xerializer.abstract_type_serializer import TypeSerializer
from jztools import numpy as pgnp
import numpy as np
import numpy.testing as npt
from numpy.lib.recfunctions import repack_fields


@dataclass
class A:
    a: int = 0
    b: int = 1


@dataclass
class B(A):
    b: int = 10


class Mock:
    def __init__(self, N=100, parent=None):
        self.value = np.arange(N)
        self.parent = parent

    def __eq__(self, mock_ser):
        return (
            np.array_equal(self.value, mock_ser.value)
            and np.array_equal(self.parent, mock_ser.parent)
            and type(mock_ser) == Mock
        )


class MockSerializer(TypeSerializer):
    handled_type = Mock

    def from_serializable(self, **kwargs):
        return self.handled_type(**kwargs)

    def as_serializable(self, obj):
        return {"N": len(obj.value), "parent": obj.parent}


class TestSerializer(TestCase):
    def test_extract_serializers(self):
        expanded_plugins = mdl.Serializer._extract_serializers([builtin_plugins])

        self.assertTrue(
            {
                getattr(builtin_plugins, x)
                for x in [
                    "DictSerializer",
                    "TupleSerializer",
                    "SetSerializer",
                    "ListDeSerializer",
                ]
            }.issubset(expanded_plugins)
        )

    def test_default_types(self):
        srl = mdl.Serializer()

        compound_obj_1 = [
            {"abc": 0, "def": 10.0},
            0.0,
            "abc",
            {"ghi": 100, "jkl": [200.0, 100, {"mno": [20, 30]}]},
            (1.0, {"abc": 123.0}, 10),
            slice(10, 2, -2),
            slice(5),
            slice(None, None, -5),
        ]

        for obj in [
            1,
            [0, 1, 2],
            {"a": 0, "b": 1, "c": 2},
            {1, 2, 3, 4},
            (1, 2, 3, 4),
            compound_obj_1,
        ]:
            self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

    def test_literal(self):
        srl = mdl.Serializer()
        for obj in [
            "abc",
            1,
            "1",
            None,
            "None",
            [1, 2, 3, {"a": 0, "b": 1, "c": ("x", "y", "z")}],
        ]:
            self.assertEqual(srl.deserialize(srl.serialize(Literal(obj))), obj)

    def test_dtype_serializer(self):
        srl = mdl.Serializer()

        for obj in [
            np.dtype("f"),
            np.dtype("datetime64"),
            np.dtype("datetime64[m]"),
            np.dtype([("fld1", "f"), ("fld2", "i")]),
            np.dtype([("fld1", ("f", (10, 40))), ("fld2", "i")]),
            np.dtype(
                [("fld1", ("f", (10, 40))), ("fld2", "i"), ("date3", "datetime64[1h]")]
            ),
        ]:
            self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

    def test_default_extensions(self):
        srl = mdl.Serializer()

        obj = slice(10, 30, 20)
        self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

        obj = np.dtype([("f0", "datetime64"), ("f1", "f8")])
        self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

        obj = [
            {"abc": 0, "def": slice(10, 30, 20)},
            0.0,
            "abc",
            {
                "ghi": 100,
                "jkl": [
                    200.0,
                    np.dtype([("f0", "datetime64"), ("f1", "f8")]),
                    {"mno": [20, 30]},
                ],
            },
            (1.0, {"abc": 123.0}, 10),
        ]
        self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

    def test_user_extensions(self):
        srl = mdl.Serializer([MockSerializer()])

        #
        obj = Mock(10)
        self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

        #
        obj = [
            {"abc": Mock(10), "def": 10.0},
            Mock(20),
            "abc",
            {"ghi": Mock(30, parent=Mock(5)), "jkl": [200.0, 100, {"mno": [20, 30]}]},
            (1.0, {"abc": 123.0}, 10),
        ]
        self.assertEqual(srl.deserialize(srl.serialize(obj)), obj)

    def test_ndarray_extension(self):
        srl = mdl.Serializer()
        for arr in [
            # np.array(0), #TODO - should work to but fails.
            np.array([]),
            np.datetime64("2020-10-10"),
            pgnp.random_array(
                (10, 5, 3), [("f0", "datetime64[m]"), ("f1", "f"), ("f2", "i")]
            ),
            np.array((10, 5, 3)),
            [{"abc": 0, "def": 1, "xyz": np.array([5, 6, 7])}],
        ]:
            serialized = srl.serialize(arr)
            self.assertIsInstance(serialized, str)
            npt.assert_equal(arr, dsrlzd := srl.deserialize(serialized))

    def test_dtype_extension(self):
        all_types = ["f", "f4", "u1", "i", "L", "datetime64[D]", "datetime64[m]"]
        dtype = [(f"f{k}", fld) for k, fld in enumerate(all_types * 2)]

        sliced_dtype = np.empty(100, dtype=dtype)[[f"f{k}" for k in range(7)]].dtype
        srlzr = mdl.Serializer()
        srlzd_sliced_dtype = srlzr.serialize(sliced_dtype)
        dsrlzd_sliced_dtype = srlzr.deserialize(srlzd_sliced_dtype)

        self.assertEqual(repack_fields(sliced_dtype), dsrlzd_sliced_dtype)

    def test_json_interface(self):
        srl = mdl.Serializer()
        for arr in [
            # np.array(0), #TODO - should work to but fails.
            np.array([]),
            np.datetime64("2020-10-10"),
            pgnp.random_array(
                (10, 5, 3), [("f0", "datetime64[m]"), ("f1", "f"), ("f2", "i")]
            ),
            np.array((10, 5, 3)),
            [{"abc": 0, "def": 1, "xyz": np.array([5, 6, 7])}],
        ]:
            with NamedTemporaryFile() as tmp_fn:
                tmp_fn = tmp_fn.name
                # dumps/loads
                npt.assert_equal(arr, srl.loads(srl.dumps(arr)))
                # dump/load
                srl.dump(arr, tmp_fn)
                npt.assert_equal(arr, srl.load(tmp_fn))

    def test_empty_file(self):
        with NamedTemporaryFile() as tmp_fo:
            tmp_fn = tmp_fo.name
            srl = mdl.Serializer()

            # Serializer.load raises an exception.
            with self.assertRaisesRegex(
                JSONDecodeError, r"Expecting value: line 1 column 1 \(char 0\)"
            ):
                srl.load(tmp_fn)

            # Serializer.load_safe, returns a boolean empty-file indicator.
            self.assertEqual(srl.load_safe(tmp_fn), (None, "empty"))

    def test_datetime_plugins(self):
        # pytz timezones
        srl = mdl.Serializer()
        for tz in [pytz.utc, pytz.timezone("US/Eastern")]:
            self.assertIs(tz, srl.deserialize(srl.serialize(tz)))

        # datetime
        for x in [
            # Datetimes
            datetime.datetime.fromisoformat("2020-10-10T10:10:10.123400"),
            datetime.datetime.fromisoformat("2020-10-10T10:10:10.123400").replace(
                tzinfo=pytz.utc
            ),
        ]:
            self.assertEqual(x, srl.deserialize(srl.serialize(x)))

    def test_time_plugins(self):
        # pytz timezones
        srl = mdl.Serializer()

        # datetime
        for x in [
            # Datetimes
            datetime.time(10, 10, 10, 12345),
            datetime.time(23),
            datetime.time(23, 1),
            datetime.time(23, 1, 1),
            datetime.time(23, 1, 1, 99999),
        ]:
            self.assertEqual(x, srl.deserialize(srl.serialize(x)))
            self.assertIsInstance(x, datetime.time)

    def test_inheritable(self):
        class ASerializer(mdl.TypeSerializer):
            inheritable = True
            handled_type = A

            def as_serializable(self, obj):
                return {"a": obj.a, "b": obj.b}

        serializer = mdl.Serializer()
        orig = [A(), B()]
        srlzd = serializer.serialize(orig)
        dsrlzd = serializer.deserialize(srlzd)
        assert dsrlzd == orig
        assert all(type(x) == type(y) for x, y in strict_zip(orig, dsrlzd))
