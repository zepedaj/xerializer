from unittest import TestCase
import numpy as np
import xerializer.numpy_plugins.array as mdl
import numpy.testing as npt
from xerializer import Serializer
from xerializer.numpy_plugins._helpers import DT64_AS_STR_DTYPE


class TestNDArraySerializer(TestCase):
    def test_count_dtype_depth(self):
        for _in_dtype, _expected_depth in [
            #
            (np.dtype("f"), 0),
            #
            (np.dtype("M8[D]"), 0),
            #
            (np.dtype("M8[m]"), 0),
            #
            (np.dtype([("f1", "f"), ("f2", "i")]), 1),
            #
            (np.dtype([("f1", "f"), ("f2", "M8[D]")]), 1),
            #
            (
                np.dtype(
                    [
                        ("f1", "f"),
                        ("f2", "M8[D]"),
                        ("f3", [("f1", "f"), ("f2", "M8[D]")]),
                    ]
                ),
                2,
            ),
            #
            (
                np.dtype(
                    [
                        ("f1", "f"),
                        ("f2", "M8[D]"),
                        ("f3", [("f1", "f", (10, 5)), ("f2", "M8[D]")]),
                    ]
                ),
                4,
            ),
        ]:
            self.assertEqual(mdl.count_dtype_depth(_in_dtype), _expected_depth)

    def test_count_list_depth(self):
        for _lst, _expected_depth in [
            ("abc", 0),
            (0.0, 0),
            ([0, 1, 2], 1),
            ([0, [0, 0], [0, 0, [0, 0]], [[[0], 0]]], 4),
        ]:
            self.assertEqual(mdl.count_list_depth(_lst), _expected_depth)

    def test_sanitize_dtype(self):
        dt64_str = DT64_AS_STR_DTYPE
        for _in_dtype, _sanitized, _sanitized_no_dt64 in [
            (np.dtype("f"), "float32", "float32"),
            (np.dtype("M8[D]"), "datetime64[D]", dt64_str),
            (np.dtype("M8[m]"), "datetime64[m]", dt64_str),
            (
                np.dtype([("f1", "f"), ("f2", "i")]),
                [("f1", "float32"), ("f2", "int32")],
                [("f1", "float32"), ("f2", "int32")],
            ),
            (
                np.dtype([("f1", "f"), ("f2", "M8[D]")]),
                [("f1", "float32"), ("f2", "datetime64[D]")],
                [("f1", "float32"), ("f2", dt64_str)],
            ),
            (
                np.dtype(
                    [
                        ("f1", "f"),
                        ("f2", "M8[D]"),
                        ("f3", [("f1", "f"), ("f2", "M8[D]")]),
                    ]
                ),
                [
                    ("f1", "float32"),
                    ("f2", "datetime64[D]"),
                    ("f3", [("f1", "float32"), ("f2", "datetime64[D]")]),
                ],
                [
                    ("f1", "float32"),
                    ("f2", dt64_str),
                    ("f3", [("f1", "float32"), ("f2", dt64_str)]),
                ],
            ),
            (
                np.dtype(
                    [
                        ("f1", "f"),
                        ("f2", "M8[D]"),
                        ("f3", [("f1", "f", (10, 5)), ("f2", "M8[D]")]),
                    ]
                ),
                [
                    ("f1", "float32"),
                    ("f2", "datetime64[D]"),
                    ("f3", [("f1", "float32", (10, 5)), ("f2", "datetime64[D]")]),
                ],
                [
                    ("f1", "float32"),
                    ("f2", dt64_str),
                    ("f3", [("f1", "float32", (10, 5)), ("f2", dt64_str)]),
                ],
            ),
        ]:
            # With datetime64
            self.assertEqual(mdl.sanitize_dtype(_in_dtype), _sanitized)
            arr1 = np.empty((3, 5), _in_dtype)
            arr2 = np.empty((3, 5), _sanitized)
            arr2[:] = arr1
            # Use str bc nan comparison fails in structured arrays.
            npt.assert_equal(str(arr1), str(arr2))

            # With datetime64 as strings
            self.assertEqual(
                _from_in_dtype := mdl.sanitize_dtype(
                    _in_dtype, datetime64_as_string=True
                ),
                _sanitized_no_dt64,
            )
            arr1 = np.empty((3, 5), _from_in_dtype)
            arr2 = np.empty((3, 5), _sanitized_no_dt64)
            arr2[:] = arr1
            # Use str bc nan comparison fails in structured arrays.
            npt.assert_equal(str(arr1), str(arr2))

    def test_array_to_list(self):
        for _arr, _arr_as_list in [
            #
            (np.array(1), 1),
            #
            (
                np.array(
                    (1, 2, "2020-10-10"), [("f0", "i"), ("f1", "f"), ("f3", "M8[D]")]
                ),
                [1, 2, "2020-10-10"],
            ),
            #
            (
                np.array(["2020-10-10", "2020-10-11", "2020-10-12"], "M8[D]"),
                ["2020-10-10", "2020-10-11", "2020-10-12"],
            ),
            #
            (
                np.array(
                    [("2020-10-12", 10, (5.0, "2020-10-13"))] * 2,
                    [
                        ("f0", "M8[D]"),
                        ("f1", int),
                        ("f3", [("f4", float), ("f5", "M8[D]")]),
                    ],
                ),
                [["2020-10-12", 10, [5.0, "2020-10-13"]]] * 2,
            ),
        ]:
            self.assertEqual(mdl.array_to_list(_arr), _arr_as_list)
            npt.assert_array_equal(
                mdl.list_to_array(
                    mdl.array_to_list(_arr), mdl.sanitize_dtype(_arr.dtype)
                ),
                _arr,
            )

    def test_list_to_array(self):
        for _dtype, dt64_posns in [
            #
            (np.dtype("f"), None),
            #
            (np.dtype("M8[D]"), [None]),
            #
            (np.dtype([("f1", "f"), ("f2", "i")]), None),
            #
            (np.dtype([("f1", "f"), ("f2", "M8[D]")]), [["f2"]]),
            #
            (
                np.dtype(
                    [
                        ("f1", "f"),
                        ("f2", "M8[D]"),
                        ("f3", [("f1", "f"), ("f2", "M8[D]")]),
                    ]
                ),
                [["f2"], ["f3", "f2"]],
            ),
            #
            (
                np.dtype(
                    [
                        ("f1", "f"),
                        ("f2", "M8[D]"),
                        ("f3", [("f1", "f", (3, 2)), ("f2", "M8[D]")]),
                    ]
                ),
                [["f2"], ["f3", "f2"]],
            ),
        ]:
            arr = np.empty((5, 3), dtype=_dtype)

            # Use array to string as NaN comparison fails in nested arrays with npt.assert_equal / npt.assert_array_equal.
            self.assertEqual(
                np.array2string(arr),
                np.array2string(
                    mdl.list_to_array(mdl.array_to_list(arr), dtype=_dtype)
                ),
            )

    def test_empty_structured(self):
        srlzd = {
            "__type__": "np.array",
            "dtype": (
                dtype := [
                    ["date", "datetime64[m]"],
                    ["open", "float32"],
                    ["high", "float32"],
                    ["low", "float32"],
                    ["close", "float32"],
                    ["trades", "float32"],
                    ["volume", "float32"],
                    ["volume_weighted_price", "float32"],
                ]
            ),
            "value": [],
        }
        serializer = Serializer()
        serializer.from_serializable(srlzd)

        dtype = [tuple(x) for x in dtype]
        npt.assert_array_equal(
            arr := np.array([], dtype),
            serializer.deserialize(serializer.serialize(arr)),
        )


class TestDatetime64(TestCase):
    def test_serialize(self):
        serializer = Serializer()
        dt64_str = DT64_AS_STR_DTYPE
        for _obj in [
            #
            np.datetime64("2020-10-10"),
            np.datetime64("2020-10-10T10:00:00.123"),
        ]:
            _dsrlzd_obj = serializer.deserialize(serializer.serialize(_obj))
            self.assertEqual(_obj, _dsrlzd_obj)
            assert _obj.dtype == _dsrlzd_obj.dtype

    def test_from_serializable(self):
        # >>> srlzr.from_serializable({'__type__':'np.datetime64', 'value':'2002-10-10'})
        # >>> srlzr.from_serializable({'__type__':'np.datetime64', 'args':['2002-10-10', 'h']})
        # >>> srlzr.from_serializable({'__type__':'np.datetime64', 'value':'2002-10-10', 'dtype':<np.dtype>})

        serializer = Serializer()
        for source, expected in [
            (
                {"__type__": "np.datetime64", "value": "2020-10-10"},
                np.datetime64("2020-10-10"),
            ),
            (
                {"__type__": "np.datetime64", "args": ["2020-10-10", "h"]},
                np.datetime64("2020-10-10", "h"),
            ),
        ]:
            self.assertEqual(actual := serializer.from_serializable(source), expected)
            self.assertEqual(actual.dtype, expected.dtype)

        with self.assertWarns(DeprecationWarning):
            for source, expected in [
                (
                    {
                        "__type__": "np.datetime64",
                        "value": "2020-10-10",
                        "dtype": {"__type__": "dtype", "value": "datetime64[m]"},
                    },
                    np.datetime64("2020-10-10", "m"),
                )
            ]:
                self.assertEqual(
                    actual := serializer.from_serializable(source), expected
                )
                self.assertEqual(actual.dtype, expected.dtype)


class TestTimedelta64(TestCase):
    def test_serialize(self):
        serializer = Serializer()
        dt64_str = DT64_AS_STR_DTYPE
        for _obj in [
            #
            np.timedelta64(20, "h"),
            np.timedelta64(10, "us"),
        ]:
            _dsrlzd_obj = serializer.deserialize(serializer.serialize(_obj))
            self.assertEqual(_obj, _dsrlzd_obj)
            assert _obj.dtype == _dsrlzd_obj.dtype

    def test_from_serializable(self):
        # >>> srlzr.from_serializable({'__type__':'np.timedelta64', 'value':20})
        # >>> srlzr.from_serializable({'__type__':'np.timedelta64', 'args':[10, 'h']})

        serializer = Serializer()
        for source, expected in [
            (
                {"__type__": "np.timedelta64", "value": 20},
                np.timedelta64(20),
            ),
            (
                {"__type__": "np.timedelta64", "args": [10, "h"]},
                np.timedelta64(10, "h"),
            ),
            (
                {"__type__": "np.timedelta64", "args": [0]},
                np.timedelta64(0),
            ),
        ]:
            self.assertEqual(actual := serializer.from_serializable(source), expected)
            self.assertEqual(actual.dtype, expected.dtype)
