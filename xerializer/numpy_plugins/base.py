from xerializer.abstract_type_serializer import TypeSerializer
from ..builtin_plugins import _BuiltinTypeSerializer
from ._helpers import sanitize_dtype
import numpy as np
from numpy.lib.format import dtype_to_descr
import base64


class DtypeSerializer(_BuiltinTypeSerializer):
    """

    By default, serialization will produce a sanitized, more human-readable but non-endiannes-preserving representation. E.f., 'float32' instead of '<f8'.

    To preserve endinannes, use
    .. code-block::

      from xserializer import Serializer
      Serializer([DTypeSerializer(sanitize=False)])

    Converts :class:`np.dtype` objects to serializables of the form

    .. code-block::

      # A base dtype
      {
        '__type__': 'numpy.dtype',
        'value': "'float32'"
      }
      # A structured dtype
      {
        '__type__': 'numpy.dtype',
        'value': "[('fld1', '<f4'), ('fld2', '<i4', (30, 20))]"
      }

    Example:
    .. ipython::

        In [16]: from xerializer import Serializer

        @doctest
        In [17]: Serializer().as_serializable(np.dtype('f'))
        Out[17]: {'__type__': 'numpy.dtype', 'value': "'float32'"}

    """

    handled_type = np.dtype

    def __init__(self, sanitize=True):
        self.sanitize = sanitize
        super().__init__()

    @classmethod
    def as_nested_lists(cls, dtype, depth=0):
        if isinstance(dtype, np.dtype):
            dtype = dtype_to_descr(dtype)
            return cls.as_nested_lists(dtype, depth + 1)
        elif isinstance(dtype, list):
            return [cls.as_nested_lists(_x, depth + 1) for _x in dtype]
        elif isinstance(dtype, tuple):
            return [dtype[0], cls.as_nested_lists(dtype[1], depth + 1)] + (
                [list(dtype[2])] if len(dtype) == 3 else []
            )
        elif isinstance(dtype, str):
            return dtype
        else:
            raise TypeError(type(dtype))

    @classmethod
    def as_nested_tuple_lists(cls, dtype, as_tuple=False):
        if isinstance(dtype, list):
            if as_tuple:
                out = [
                    dtype[0],
                    cls.as_nested_tuple_lists(dtype[1], as_tuple=False),
                ] + ([tuple(dtype[2])] if len(dtype) == 3 else [])
                out = tuple(out)
            else:
                out = [cls.as_nested_tuple_lists(_x, as_tuple=True) for _x in dtype]

            return out
        elif isinstance(dtype, str):
            return dtype
        else:
            raise TypeError(type(dtype))

    def as_serializable(self, obj):
        # return {'value': Literal(dtype_to_descr(obj)).encode()}
        obj = sanitize_dtype(obj) if self.sanitize else obj
        return {"value": self.as_nested_lists(obj)}

    def from_serializable(self, value):
        # return descr_to_dtype(Literal.decode(value))
        return np.dtype(self.as_nested_tuple_lists(value))


class DtypeSerializer_npvoid(DtypeSerializer):
    # Numpy versions above 19 have a special type for structured dtype
    handled_type = type(np.dtype([("a", "f")]))


class NDArrayAsBytesSerializer(_BuiltinTypeSerializer):

    handled_type = np.ndarray
    signature = "np.array_as_bytes"

    def as_serializable(self, arr):
        from jztools.numpy import encode_ndarray

        return {"bytes": base64.b64encode(encode_ndarray(arr)).decode("ascii")}

    def from_serializable(self, bytes):
        from jztools.numpy import decode_ndarray

        return decode_ndarray(base64.b64decode(bytes.encode("ascii")))


class Datetime64AsBytesSerializer(NDArrayAsBytesSerializer):
    handled_type = np.datetime64
    signature = "np.datetime64_as_bytes"
