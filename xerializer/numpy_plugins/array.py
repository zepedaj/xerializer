from .base import DtypeSerializer
import warnings
import re
from xerializer.builtin_plugins import _BuiltinTypeSerializer
from jztools.py import strict_zip
from datetime import date, datetime
import numpy as np
from numbers import Number
from ._helpers import sanitize_dtype


def array_to_list(arr, nesting=0):
    # Deals with two issues with ndarray.tolist(). (The datetime64 issue) The first is numpy.ndarray.tolist converts datetime64 objects to datetime objects, not ISO date strings, which are more human-friendly. (The tuple issue) The second is that structured arrays will result in (nested) lists of tuples, and these tuple format is required when going back from a list to a structure array. Tuples cannot be represented in serialized formats by default, and using a typed representation (e.g., {'__type__':'tuple', '__value__':[0,1,2]}) is too verbose (e.g., relative to [0,1,2]), especially with nested tuples. Hence this function represents an array as a list of nested base types and lists.
    #
    # Example outputs of ndarray.tolist illustrating these two points:
    #
    # (The datetime64 issue)
    # In [63]: np.array(['2020-10-10'], dtype='datetime64[D]').tolist()
    # Out[63]: [datetime.date(2020, 10, 10)]
    #
    # (The tuple issue)
    # In [67]: np.array([(10, '2020-10-10')], dtype=[('id',int), ('date', 'datetime64[D]')]).tolist()
    # Out[67]: [(10, datetime.date(2020, 10, 10))]
    #
    # Need to account for possibly nested tuples (dtypes of dtypes) possibly containing datetime strings.

    # First possibility
    if isinstance(arr, (str, Number)) or arr is None:
        return arr
    elif isinstance(arr, (date, datetime)):
        return arr.isoformat()
    elif isinstance(arr, (tuple, list)):
        return [array_to_list(_x, nesting + 1) for _x in arr]
    elif isinstance(arr, (np.ndarray, np.datetime64)):
        return array_to_list(arr.tolist(), nesting + 1)
    else:
        raise TypeError(
            f"Invalid type {type(arr)} found in input container at nested level {nesting}."
        )

    # # Second possibility. Faster?
    # return json.loads(json.dumps(literal_eval(np.array2string(
    #     arr, formatter={'float_kind': lambda x: "%.18g" % x}, separator=', '))))


def count_dtype_depth(dtype):
    if isinstance(dtype, np.dtype):
        return count_dtype_depth(sanitize_dtype(dtype))
    elif isinstance(dtype, list):
        return 1 + max((count_dtype_depth(_sub_dtype) for _sub_dtype in dtype))
    elif isinstance(dtype, tuple):
        sub_type_name, sub_dtype, sub_dtype_shape = (list(dtype) + [[]])[:3]
        return count_dtype_depth(sub_dtype) + len(sub_dtype_shape)
    else:
        return 0


def count_list_depth(container):
    if isinstance(container, list):
        return 1 + max(
            (count_list_depth(sub_container) for sub_container in container), default=0
        )
    else:
        return 0


def nested_lists_to_mixed(container, sanitized_dtype, cutoff_depth, curr_depth=0):
    """
    Helper function for _list_to_array.
    """
    if isinstance(container, list):
        if curr_depth < cutoff_depth:
            # Traversing dimensions of array.
            return [
                (
                    nested_lists_to_mixed(
                        _x, sanitized_dtype, cutoff_depth, curr_depth + 1
                    )
                    if isinstance(_x, list)
                    else _x
                )
                for _x in container
            ]
        else:
            # Traversing nested dtypes.
            return tuple(
                [
                    _list_to_array(_x, _sntzd_sub_dt[1])
                    for _x, _sntzd_sub_dt in strict_zip(container, sanitized_dtype)
                ]
            )

    else:
        return container


def _list_to_array(arr_list, sanitized_dtype):
    """
    Helper function for list_to_array.
    """

    dtype_depth = count_dtype_depth(sanitized_dtype)
    arr_depth = count_list_depth(arr_list)
    arr_list = nested_lists_to_mixed(arr_list, sanitized_dtype, arr_depth - dtype_depth)
    return arr_list


def list_to_array(arr_list, dtype):
    """
    Converts a nested list containing no tuples, to one containing a mixture of lists and tuples determined by the specified dtype.
    """
    sanitized_dtype = sanitize_dtype(dtype)
    if arr_list:
        arr_list = _list_to_array(arr_list, sanitized_dtype)
    return np.array(arr_list, dtype=sanitized_dtype)


class NDArraySerializer(_BuiltinTypeSerializer):
    """
    Numpy array serialization. Supports reading hand-written serializations with implicit dtype (to be deduced by numpy).
    """

    signature = "np.array"
    handled_type = np.ndarray
    _dtype_serializer = DtypeSerializer()

    def as_serializable(self, arr):
        return {
            "dtype": self._dtype_serializer.as_serializable(sanitize_dtype(arr.dtype))[
                "value"
            ],
            "value": array_to_list(arr),
        }

    def from_serializable(self, value, dtype=None):
        if dtype is not None:
            dtype = self._dtype_serializer.from_serializable(dtype)
            out = list_to_array(value, dtype)
        else:
            out = np.array(value)
        return out


class _NoArg:
    pass


class _Datetime64AndTimeDelta64Serializer_Base(_BuiltinTypeSerializer):
    _name: str
    signature: str
    handled_type: np.dtype

    def from_serializable(self, value=_NoArg, args=_NoArg, dtype=_NoArg):
        if (sum([value is _NoArg, args is _NoArg])) != 1 or (
            dtype is not _NoArg and args is not _NoArg
        ):
            raise ValueError(f"Invalid arguments.")
        if value is not _NoArg:
            out = self.handled_type(value)
            if dtype is not _NoArg:
                out = out.astype(dtype)
                warnings.warn("Argument `dtype` is deprecated.", DeprecationWarning)
            return out
        else:
            return self.handled_type(*args)


class Datetime64Serializer(_Datetime64AndTimeDelta64Serializer_Base):
    """
    Can read both types of representations:

    .. doctest::

      >>> from xerializer import Serializer
      >>> srlzr = Serializer()
      >>> srlzr.from_serializable({'__type__':'np.datetime64', 'value':'2002-10-10'})
      >>> srlzr.from_serializable({'__type__':'np.datetime64', 'args':['2002-10-10', 'h']})
    """

    _name = "datetime64"
    signature = "np.datetime64"
    handled_type = np.datetime64

    def _get_specifier(self, dtype):
        return re.fullmatch(self._name + r"\[(?P<spec>.*)\]", str(dtype))["spec"]

    def as_serializable(self, val):
        specifier = self._get_specifier(val.dtype)
        return {"args": ([str(val)] + ([specifier] if specifier else []))}


class Timedelta64Serializer(_Datetime64AndTimeDelta64Serializer_Base):
    """
    Can read both types of representations:

    .. doctest::

      >>> from xerializer import Serializer
      >>> srlzr = Serializer()
      >>> srlzr.from_serializable({'__type__':'np.timedelta64', 'value':20})
      >>> srlzr.from_serializable({'__type__':'np.timedelta64', 'args':[10, 'h']})
    """

    _name = "timedelta64"
    signature = "np.timedelta64"
    handled_type = np.timedelta64

    def _get_specifier(self, dtype):
        return re.fullmatch(self._name + r"(\[(?P<spec>.*)\])?", str(dtype))["spec"]

    def as_serializable(self, val):
        specifier = self._get_specifier(val.dtype)
        return {"args": ([val.astype(int).item()] + ([specifier] if specifier else []))}
