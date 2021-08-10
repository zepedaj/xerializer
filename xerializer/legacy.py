from .abstract_type_serializer import TypeSerializer
from numpy import dtype, ndarray, datetime64
from numpy.lib.format import dtype_to_descr, descr_to_dtype
import base64


class SliceSerializer(TypeSerializer):

    handled_type = None
    as_serializable = None
    signature = 'pglib.serializer.extensions.SliceSerializer'

    @classmethod
    def from_serializable(cls, __value__):
        return slice(*__value__)


class DtypeSerializer(TypeSerializer):

    handled_type = None
    as_serializable = None
    signature = 'pglib.serializer.extensions.DtypeSerializer'

    @classmethod
    def from_serializable(cls, __value__):
        return descr_to_dtype(__value__)


class NDArraySerializer(TypeSerializer):

    handled_type = None
    as_serializable = None
    signature = 'pglib.serializer.extensions.NDArraySerializer'

    @classmethod
    def from_serializable(cls, __value__):
        from pglib.numpy import decode_ndarray
        return decode_ndarray(base64.b64decode(__value__.encode('ascii')))


class TupleSerializer(TypeSerializer):
    handled_type = None
    as_serializable = None
    signature = 'builtins.tuple'

    @classmethod
    def from_serializable(cls, __value__):
        return tuple(__value__)


class SetSerializer(TypeSerializer):
    handled_type = None
    as_serializable = None
    signature = 'builtins.set'

    @classmethod
    def from_serializable(cls, __value__):
        return set(__value__)
