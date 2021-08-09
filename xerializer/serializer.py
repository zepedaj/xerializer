"""

Serialization
---------------

The serialization protocols implemented by this module have the following aims:

* **Readability** / ease of **manual editing** of serialized format.
* Ease of **extensibility** with minimal coding overhead - Classes can become serializable by deriving from :class:`~xerializer.Serializable` and implementing :meth:`~xerializer.Serializable.as_serializable` and optionally :meth:`~xerializer.Serializable.from_serializable`.
* **Code unobstrusiveness** - Custom objects can also be made serializable by instead implementing a stand-alone :class:`~xerializer.TypeSerializer`, setting :attr:`~xerializer.TypeSerializer.handled_type` to the class to make serializable.
* **Syntax unobtrusiveness** - JSON/YAML-compatible base types (numeric types, ``list``, ``dict``) are converted to serializable objects without any added verbosity :ref:`[1]<Syntax Overhead>` . Custom serializable types are serialized as dictionaries with a ``__type__``.
* **Builtin type** (``tuple``, ``set``, ``slice``) support out-of-the-box.
* **Numpy** support (``numpy.dtype``,  ``numpy.ndarray``), including (nested and/or shaped) structured dtypes out-of-the-box.
* **Safety** - Only :class:`~xerializer.Serializable` objects or those with a :class:`~xerializer.TypeSerializer` will be deserialized into objects by :class:`~xerializer.Serializer`, and users have fine-grained control of enabled third-party and builtin plugins.

Syntax
--------
The contents or :attr:`__args__` and :attr:`__kwargs__` can be any serializable type. When pre-fixed by ``'@py:'``, they can also be string representation of standard python objects (``byte``, ``tring``, ``int``, ``float``, ``list``, ``tuple``, ``set``, ``dict``, and any other supported by python's :meth:`ast.literal_eval`).

Syntax Overhead
----------------
JSON/YAML-compatible base types are converted to serializable objects without any added verbosity. The exception is dictionaries that contain the key ``__type__``. Such dictinoaries are represented in the following more verbose form:

.. code-block::

  {'__type__': 'dict',
   'value': <original dictionary>}



Composibility
---------------

"""

from numbers import Number
from . import builtin_plugins as builtin_plugins_module
from .abstract_type_serializer import _SerializableSerializer
from . import numpy_plugins
from pglib.py import filelike_open
import json
from ._registered import _REGISTERED_AS_SERIALIZABLE_PLUGINS, _REGISTERED_FROM_SERIALIZABLE_PLUGINS
from typing import Union


class ExtensionMissing(TypeError):
    def __init__(self, signature):
        super().__init__(
            f"No installed handler for types with signature {signature}.")


class UnserializableType(TypeError):
    def __init__(self, in_type):
        super().__init__(
            f"Type {in_type} cannot be serialized by the installed extensions.")


class Serializer:
    """
    Extension of JSON serializer that also supports objects implementing or being supported by a :class:`~pglib2.abstract_type_serializer.TypeSerializer` interface as well as lists, tuples, sets and dictionaries (with string keys) of such objects. Note that, unlike the default json behavior, :class:`Serializer` preserves types such as tuple and list.

    Default extensions include :class:`slice` objects and :class:`numpy.dtype` objects.
    """

    def __init__(self, plugins: Union[list, dict] = None,
                 precedence=('builtin', 'numpy', 'plugins', 'third_party')):
        """
        :param plugins: List of unregistered plugins to use as type serializers. Can also be a dictionary with keys 'as_serializable' and 'from_serializable' to specify plugins that will only be used for serialization and deserialization, respectively.
        :param precedence: Plugin order of precedence. Highest order of precedence plugins overwrite those with the same signature or handled type. Should be a list containing all or some of ['builtin', 'numpy', 'plugins', 'third_party']. Excluding elements from this list will also exclude the corresponding group of plugins.
        """

        all_plugins = {}

        if isinstance(
                plugins, dict) and not set(
                plugins.keys()).issubset(
                ['as_serializable', 'from_serializable']):
            raise Exception(
                "Expected plugins to be a list or dictionary with keys from ['as_serializable', 'from_serializable'].")
        all_plugins['plugins'] = plugins or []

        all_plugins['builtin'] = ([getattr(builtin_plugins_module, name)() for name in [
            'DictSerializer', 'TupleSerializer', 'SetSerializer', 'SliceSerializer',
        ]] + [_SerializableSerializer.create_derived_class(builtin_plugins_module.Literal)()
              ]) if 'builtin' in precedence else []

        all_plugins['numpy'] = [getattr(numpy_plugins, name)() for name in [
            'DtypeSerializer', 'NDArraySerializer',
            # 'NDArrayAsBytesSerializer', 'Datetime64AsBytesSerializer'
        ]] if 'numpy' in precedence else []

        all_plugins['third_party'] = {
            'as_serializable': _REGISTERED_AS_SERIALIZABLE_PLUGINS,
            'from_serializable': _REGISTERED_FROM_SERIALIZABLE_PLUGINS}

        self.as_serializable_plugins = {}
        self.from_serializable_plugins = {}

        for plugin_group_name in precedence[::-1]:

            plugin_group = all_plugins[plugin_group_name]
            if isinstance(plugin_group, list):
                plugin_group = {'as_serializable': plugin_group,
                                'from_serializable': plugin_group}

            self.as_serializable_plugins.update({
                _x.handled_type: _x for _x in plugin_group['as_serializable']
                if _x.as_serializable})

            self.from_serializable_plugins.update({
                _x.signature: _x for _x in plugin_group['from_serializable']
                if _x.from_serializable})

    @ classmethod
    def register_custom_serializer(
            cls,
            type_serializer,
            as_serializable=True,
            from_serializable=True):
        """
        :param type_serializer: The type serializer to register. Should derive from :class:`~pglib2.serializer2.abstract_type_serializer.Serializer`
        :param as_serializable: If ``True`` and ``type_serializer.as_serializable != None``, register this type serializer for serialization.
        :param from_serializable: If ``True`` and ``type_serializer.from_serializable != None``, register this type serializer for deserialization.
        """
        if as_serializable and type_serializer.as_serializable is not None:
            cls.as_serializable_plugins[type_serializer.handled_type] = type_serializer
        if from_serializable and type_serializer.from_serializable is not None:
            cls.from_serializable_plugins[type_serializer.signature] = type_serializer

    def as_serializable(self, obj):

        if isinstance(obj, (Number, str, type(None))):
            # Simple types
            return obj
        elif isinstance(obj, list):
            # Lists
            srlzd_obj = [self.as_serializable(_val) for _val in obj]
            return srlzd_obj
        else:
            # Dictionaries and plugins
            try:
                type_serializer = self.as_serializable_plugins[type(obj)]
            except KeyError:
                raise UnserializableType(type(obj))
            else:
                return type_serializer._build_typed_dict(obj, self.as_serializable)

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
