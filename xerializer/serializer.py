"""
:class:`Serializer` class implementation.
"""

from inspect import isabstract
from itertools import chain
from numbers import Number
from . import builtin_plugins
from .numpy_plugins import numpy_serializers, numpy_as_bytes_serializers  # noqa
from pglib.py import filelike_open
import json
from ._registered import _THIRD_PARTY_PLUGINS
from typing import TypeVar, Optional, List, Union
from types import ModuleType
from . import datetime_plugins
from .abstract_type_serializer import TypeSerializer


class ExtensionMissing(TypeError):
    def __init__(self, signature):
        super().__init__(
            f"No installed handler for types with signature {signature}.")


class UnserializableType(TypeError):
    def __init__(self, in_obj):
        super().__init__(
            f"Object {in_obj} of type {type(in_obj)} cannot be serialized by the installed extensions.")


PluginsType = TypeVar(Optional[List[Union[TypeSerializer, ModuleType]]])
"""
Can be a ``None`` or a list containing :class:`TypeSerializer` class definitions or their modules.
"""


class Serializer:
    """
    Extension of JSON serializer that also supports objects implementing or being supported by a :class:`~pglib2.abstract_type_serializer.TypeSerializer` interface as well as lists, tuples, sets and dictionaries (with string keys) of such objects. Note that, unlike the default json behavior, :class:`Serializer` preserves types such as tuple and list.

    Default extensions include :class:`slice` objects and :class:`numpy.dtype` objects.
    """

    def __init__(self,
                 plugins: PluginsType = None,
                 builtins: bool = True,
                 third_party: bool = True,
                 numpy_as_bytes: bool = False):
        """
        :param plugins: List of :class:`TypeSerializer` classes or modules containing such classes. Will overwrite any builting serializers managing the same handled type or signature.
        :param builtins: Whether to include the builtin plugins in the serializer.
        :param third_party: Whether to include all registered third-party serializers.
        :param numpy_as_bytes: When ``builtins=True``, setting this to ``True`` will serialize numpy arrays in a more compact byte representation that is not human readable/editable. The default uses a human-readable/editable string representation.

        .. todo:: Add tests to ensure plugins override builtins.
        """

        # Assemble all serializers
        plugins = plugins or []
        builtins = [numpy_serializers if not numpy_as_bytes else numpy_as_bytes_serializers,
                    builtin_plugins, datetime_plugins] if builtins else []
        third_party = _THIRD_PARTY_PLUGINS if third_party else []
        all_serializers = [
            _x() if self._is_type_serializer_subclass(_x) else _x
            for _x in self._extract_serializers(builtins + third_party + plugins)]

        # Register serializers with object
        self.as_serializable_plugins = {
            x.handled_type: x for x in all_serializers if x.as_serializable}
        self.from_serializable_plugins = {
            _alias: x for x in all_serializers if x.from_serializable
            for _alias in ([x.signature] + (x.aliases or []))}

    @classmethod
    def _is_type_serializer_subclass(cls, _srlzr):
        return (isinstance(_srlzr, type) and
                issubclass(_srlzr, TypeSerializer) and
                not isabstract(_srlzr))

    @classmethod
    def _extract_serializers(cls, plugins: PluginsType):
        """
        Concatenates all lists in plugins into a single list of classes, expanding modules into their classes of type :class:`TypeSerializer`.
        """

        return list(chain(*list(
            # Expand module
            [_srlzr for _srlzr in vars(_x).values() if cls._is_type_serializer_subclass(_srlzr)]
            if isinstance(_x, ModuleType)
            # Entry is a TypeSerializer class or some other object
            else [_x]
            for _x in plugins))) if plugins else []

    def as_serializable(self, obj):

        if isinstance(obj, (Number, str, type(None))):
            # Simple types
            return obj
        elif type(obj) is list:
            # Lists
            srlzd_obj = [self.as_serializable(_val) for _val in obj]
            return srlzd_obj
        else:
            # Dictionaries and plugins
            try:
                type_serializer = self.as_serializable_plugins[type(obj)]
            except KeyError:
                raise UnserializableType(obj)
            else:
                return type_serializer._build_typed_dict(obj, self.as_serializable)

    def is_serializable(self, obj):
        return type(obj) in self.as_serializable_plugins

    def from_serializable(self, obj):

        if isinstance(obj, (Number, str, type(None))):
            # Simple types
            return obj

        elif isinstance(obj, list):
            # Lists
            return [self.from_serializable(_val) for _val in obj]

        elif isinstance(obj, dict):
            # Dictionaries and plugins
            if (signature := obj.get('__type__', None)):
                try:
                    type_deserializer = self.from_serializable_plugins[signature]
                except KeyError:
                    raise ExtensionMissing(signature)
                else:
                    return type_deserializer._build_obj(obj, self.from_serializable)

            else:
                # Dictionaries without a '__type__' field - special case to reduce verbosity in
                # the most common dictionary cases.
                return self.from_serializable_plugins['dict']._build_obj(
                    obj, self.from_serializable)
        else:
            raise TypeError(f'Invalid input of type {type(obj)}.')

    def get_signature(self, entity):
        """
        Returns the signature for the specified class.
        """
        for key, val in self.from_serializable_plugins.items():
            if val.handled_type == entity:
                return key
        raise Exception(f'Entity {entity} cannot be serialized by the installed extensions.')

    def serialize(self, obj, *args, **kwargs):
        return json.dumps(self.as_serializable(obj), *args, **kwargs)

    def deserialize(self, obj, *args, **kwargs):
        return self.from_serializable(json.loads(obj, *args, **kwargs))

    # JSON-like interface
    loads = deserialize
    dumps = serialize

    def load(self, filelike, *args, **kwargs):
        with filelike_open(filelike, 'r') as fo:
            return self.from_serializable(json.load(fo, *args, **kwargs))

    def load_safe(self, filelike, *args, **kwargs):
        """
        Similar to load, but with no errors on empty files. Returns (obj, 'success') on success,  (None, 'empty') if the file is empty, or (None, 'missing') if the file does not exist.
        """

        fo_cm = filelike_open(filelike, 'r')
        try:
            fo = fo_cm.__enter__()
        except FileNotFoundError:
            return (None, 'missing')
        else:
            with filelike_open(filelike, 'r') as fo:
                try:
                    obj = json.load(fo, *args, **kwargs)
                except json.JSONDecodeError as err:
                    if str(err) == r'Expecting value: line 1 column 1 (char 0)':
                        return (None, 'empty')
                    else:
                        raise
                else:
                    return (self.from_serializable(obj), 'success')
        finally:
            fo_cm.__exit__(None, None, None)

    def dump(self, obj, filelike, *args, **kwargs):
        with filelike_open(filelike, 'w') as fo:
            json.dump(self.as_serializable(obj), fo, *args, **kwargs)
