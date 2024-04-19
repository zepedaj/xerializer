from .abstract_type_serializer import (
    TypeSerializer,
    Serializable,
    _SerializableSerializer,
)
from jztools.py import entity_name, entity_from_name
import base64
from ast import literal_eval
from abc import ABCMeta


class _BuiltinTypeSerializer(TypeSerializer):
    # Registration  will be done by Serializer.__init__
    register = False

    @property
    def signature(self):
        return self.handled_type.__name__


class _BuiltinSerializable(Serializable):
    # Registration  will be done by Serializer.__init__
    register = False

    @classmethod
    def get_signature(cls):
        return cls.signature or cls.__name__


class Literal(_BuiltinSerializable):
    """
    Wraps a literal python expression and makes it serializable as a string. Literal python expressions can be composed of base types (e.g., ``int``, ``float``, ``list``, ``tuple``, ``dict``, ``set``).

    Note that de-serialization behaves differently for this class, as :meth:`from_serializable` produces a python expression and not a :class:`Literal` object.
    """

    def __init__(self, value, check=True):
        self.value = value
        if check:
            self.check()

    def __str__(self):
        return f"Literal({self.as_serializable()})"

    def check(self):
        if literal_eval(self.encode()) != self.value:
            raise ValueError(f"Non-invertible input {self.value}.")

    def encode(self):
        if isinstance(self.value, str):
            str_value = f"'{self.value}'"
        else:
            str_value = str(self.value)
        return str_value

    @classmethod
    def decode(self, str_value: str):
        return literal_eval(str_value)

    def as_serializable(self):
        return {"value": self.encode()}

    @classmethod
    def from_serializable(cls, value):
        return cls.decode(value)


class _LiteralSerializer(_SerializableSerializer):
    handled_type = Literal
    register = False


class DictSerializer(_BuiltinTypeSerializer):
    """
    Implicit and explicit dictionary serialization.

    .. todo:: :meth:`from_serializable` supports hashable objects as keys, but not :meth:`as_serializable`.

    @doctest
    .. ipython::

        In [9]: from xerializer import Serializer

        # Implicit serialization (less verbose).
        In [10]: Serializer().as_serializable({'a':0, 'b': 1})
        Out[10]: {'a': 0, 'b': 1}

        # Explicit serialization (more verbose - used when '__type__' is a key).
        In [11]: Serializer().as_serializable({'__type__':2, 'a':0, 'b': 1})
        Out[11]: {'__type__': 'dict', '__value__': {'a': 0, 'b': 1, '__type__': 2}}
    """

    handled_type = dict
    signature = "dict"

    def _build_typed_dict(self, obj, as_serializable):

        val = {
            _key: as_serializable(_val)
            for _key, _val in self.as_serializable(obj).items()
        }

        if "__type__" in val:
            return {"__type__": self.signature, "value": val}
        else:
            return val

    def _build_obj(self, obj, from_serializable):
        if "__type__" in obj:
            if not set(obj.keys()).issubset(valid_keys := {"__type__", "value"}):
                raise ValueError(
                    f"Invalid keys `{list(obj.keys())}` for dictionary in serializable form. Valid keys are `{list(valid_keys)}`."
                )
            if isinstance(value := obj.get("value", {}), dict):
                # obj['value'] = {<key including '__type__'> :<value to deserialize>, ...}
                value = {_key: from_serializable(_val) for _key, _val in value.items()}
            else:
                # obj['value'] = [[<key to deserialize>, <value to deserialize>], ... ]
                #                (or any other dict()-compatible arg).
                value = dict(from_serializable(value))
        else:
            # obj = {<key not including '__type__'> :<value to deserialize>, ...}
            value = {_key: from_serializable(_val) for _key, _val in obj.items()}

        return value

    def as_serializable(cls, obj):
        return obj

    def from_serializable(cls, value):
        return value


class TupleSerializer(_BuiltinTypeSerializer):
    """
    Tuple serialization.

    .. ipython::

        In [1]: from xerializer import Serializer

        In [2]: Serializer().as_serializable((1,2,'abc',True))
        Out[2]: {'__type__': 'tuple', '__value__': [1, 2, 'abc', True]}
    """

    handled_type = tuple

    def as_serializable(self, obj):
        return {"value": list(obj)}

    def from_serializable(self, value):
        return self.handled_type(value)


class SetSerializer(TupleSerializer):
    """
    Set serialization.

    @doctest
    .. ipython::

        In [1]: from xerializer import Serializer

        In [2]: Serializer().as_serializable({1,2,'abc',True})
        Out[2]: {'__type__': 'set', '__value__': [1, 2, 'abc']}

    """

    handled_type = set


# Provided for consistenty, not required. The standard syntax [1,2,3] is used by default for serialization, but the typed syntax is understood for deserialization.
class ListDeSerializer(TupleSerializer):
    handled_type = list
    as_serializable = None


class SliceSerializer(_BuiltinTypeSerializer):
    """
    Slice serialization.

    @doctest
    .. ipython::

        In [1]: from xerializer import Serializer

        In [2]: Serializer().as_serializable(slice(None,-10, -2))
        Out[2]: {'__type__': 'slice', 'stop': -10, 'step': -2}

    """

    handled_type = slice

    def as_serializable(cls, obj):
        return {
            _key: _val
            for _key in ["start", "stop", "step"]
            if (_val := getattr(obj, _key)) is not None
        }

    def from_serializable(cls, start=None, stop=None, step=None):
        return slice(start, stop, step)


class BytesSerializer(_BuiltinTypeSerializer):
    """
    Bytes serialization.
    """

    handled_type = bytes

    def as_serializable(self, obj: bytes):
        return {"value": base64.b64encode(obj).decode("ascii")}

    def from_serializable(self, value):
        return base64.b64decode(value.encode("ascii"))


class ClassSerializer(_BuiltinTypeSerializer):
    """
    Type serialization.
    """

    handled_type = type
    signature = "class"

    def as_serializable(self, obj: type):
        return {"value": entity_name(obj)}

    def from_serializable(self, value):
        return entity_from_name(value)


class ABCMetaSerializer(ClassSerializer):
    handled_type = ABCMeta
    from_serializable = None
