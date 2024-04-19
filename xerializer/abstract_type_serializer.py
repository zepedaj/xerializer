"""

.. todo::

  * Add unit tests to ensure automatic registration mechanism works.
  * Create an @serializable class decorator that assumes the __init__ function takes only serializables. Arguments in the @serializable can be similar to those in class Serializable.

"""

import abc
from jztools.py import entity_name
from inspect import isabstract
from ._registered import register_custom_serializer
from typing import Dict, Any, Optional, List, Type
from inspect import ismethod


def default_signature(cls):
    return entity_name(cls)


class TypeSerializer(abc.ABC):
    """
    Generic object serializer. A target class to serialize can inherit form this class or be handled with a standalone class that implements this interface. In the second case, class method :meth:`check_type` needs to be overloaded.
    """

    register: bool = True
    """
    Whether to automatically register this class with :class:`~xerializer.Serializer`. Defaults to True.
    """

    aliases: Optional[List[str]] = None
    """
    A list of alternate signatures that this :class:`TypeSerializer` also handles. These can be modified before instantiating any :class:`Serializer`.
    """

    inheritable: bool = False
    """
    Specifies whether the type serializer will handle derived types.
    """

    polymorphic: bool = False
    """
    If ``True``, :meth:`as_serializable` can return a dictionary with arbitrary key ``'__type__'``.
    """

    def __init__(self):
        self.aliases = list(self.aliases or [])

    @classmethod
    def for_derived_class(cls, child_handled_class) -> Type["TypeSerializer"]:
        # Derive a new type -- supports inheritable type serializers
        class DerivedTypeSerializer(cls):
            handled_type = child_handled_class

        return DerivedTypeSerializer()

    def _build_typed_dict(self, obj, as_serializable):
        kwargs = self.as_serializable(obj)
        if not self.polymorphic and "__type__" in kwargs:
            raise Exception(
                "Found reserved key '__type__' in the keyword args returned by method `as_serializable` when the serializer is not `polymorphic`."
            )
        try:
            kwargs_items = kwargs.items()
        except AttributeError:
            raise TypeError(
                f"Method {type(self).as_serializable} should return a ``Dict[str,Any]`` but instead returned a {type(kwargs)}."
            )
        else:
            return {
                "__type__": self.signature,  # Might be overwritten by the output of as_serializable if polymorphic=True
                **{_key: as_serializable(_val) for _key, _val in kwargs_items},
            }

    def _build_obj(self, typed_dict, from_serializable):
        kwargs = {
            _key: from_serializable(_val)
            for _key, _val in typed_dict.items()
            if _key != "__type__"
        }
        return self.from_serializable(**kwargs)

    @property
    def signature(self):
        """
        Property containing the string used in the :attr:`__type__` field of the serializable object. This can be any string. By default it is the fully-qualified name of the handled type.
        """
        return default_signature(self.handled_type)

    @property
    @abc.abstractmethod
    def handled_type(self):
        """
        Returns the type that this class serializes and deserializes.
        """

    @abc.abstractmethod
    def as_serializable(self, obj) -> Dict[str, Any]:
        """
        Returns a dictionary of objects that are serializable with :class:`xerializer.Serializer` (including all python base types like) and that will be passed as keyword args to method :meth:`from_serializable` when deserializing the object. The keys of these dictionary, together with key '__type__' having value , will constitute the serialization of this object.

        Set this method to ``None`` if serialization is not supported by this serializer (e.g., to support legacy signature). Such classes will only be registerd for deserialization by :class:`xerializer.Serializer`.

        :param obj: The object to convert to a serializable.
        """
        # This function is meant to make it easy for extension developers to create new plugins without needing to worry about serializable-ing components of their data structure.

    def from_serializable(self, **kwargs):
        """
        Takes the dictionary produced by :meth:`as_serializable` as keyword arguments and produces the original object. By default, this calls the ``__init__`` of the handled type.
        """
        return self.handled_type(**kwargs)

    def __init_subclass__(cls, register_meta=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._decide_register(cls, register_meta):
            register_custom_serializer(cls())

    @staticmethod
    def _decide_register(cls, register_meta):
        if not isabstract(cls) and (
            register_meta or (register_meta is None and cls.register)
        ):
            return True
        elif register_meta:
            # Ideally, this exception message should include the names of the missing methods.
            # But cls.__abstractmethods__ raises an AttributeError at this point in the class
            # creation...
            raise Exception(f"Cannot register abstract class {cls}.")
        return False


class _SerializableSerializer(TypeSerializer):
    """
    Type serializer for custom :class:`Serializable` types.
    """

    @property
    @abc.abstractmethod
    def handled_type(self) -> Type:
        pass

    @property
    def signature(self):
        return self.handled_type.get_signature()

    @property
    def inheritable(self):
        return self.handled_type.inheritable

    @property
    def polymorphic(self):
        return self.handled_type.polymorphic

    def as_serializable(self, obj):
        return obj.as_serializable()

    def from_serializable(self, **kwargs):
        return self.handled_type.from_serializable(**kwargs)

    @classmethod
    def create_derived_class(cls, handled_type, name=None, **attributes):
        name = name or (f"_{handled_type.__name__}_Serializer")
        return type(
            name,
            (cls,),
            {"handled_type": handled_type, "__module__": __name__, **attributes},
        )


class Serializable(abc.ABC):
    """
    Base class to make custom classes serializable. Classes deriving from this class are by default automatically registered with :class:`xerializer.Serializer`. Note that :class:`Serializable` uses the same metaclass as :class:`abc.ABC`, so one should not also derive from :class:`abc.ABC` when creating an abstract :class:`Serializable` child class (doing so will result in metclass errors).
    """

    signature = None
    """
    A class-level property (``None`` or ``str``, no :attr:`@property`-decorated methods allowed) specifying the string to use in the :attr:`__type__` field of the serialized representation. The actual signature is produced by classmethod :meth:`get_signature`.
    """

    register = True
    """
    A class-level property specifying whether to register this with class or not with :class:`xerializer.Serializer`.
    """

    inheritable = False
    """
    A class-level property specifying whether derived classes are also automatically serializable.
    """

    polymorphic: bool = False
    """
    If ``True``, :meth:`as_serializable` can return a dictionary with arbitrary key ``'__type__'``.
    """

    @classmethod
    def get_signature(cls):
        """
        Classmethod returning the signature for the class. Returns :attr:`signature` or the fully-qualified name of the class.
        """
        return cls.signature or default_signature(cls)

    @abc.abstractmethod
    def as_serializable(self) -> Dict[str, Any]:
        """
        Carries out the same function as :meth:`TypeSerializer.as_serializable` but for the current object (``self``).
        """
        pass

    @classmethod
    def from_serializable(cls, **kwargs):
        """
        Returns an object of this class. By default, calls ``__init__`` with the provided keywords.

        (See :meth:`TypeSerializer.from_serializable`)
        """
        try:
            return cls(**kwargs)
        except Exception as error:
            raise Exception(
                f"Failed deserializing type {cls} ({error}). See above error."
            )

    def __init_subclass__(cls, register_meta=None, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls.from_serializable and not ismethod(cls.from_serializable):
            raise Exception(
                f"Did you forget to decorate method 'from_serializable' from class {cls} with @classmethod?"
            )

        if not ismethod(cls.get_signature):
            raise Exception(
                f"Did you forget to decorate method 'get_signature' from class {cls} with @classmethod?"
            )

        if not isinstance(cls.signature, (str, type(None))):
            raise Exception(
                f"Error with 'signature' property definition for class {cls} : Serializables (unlike TypeSerializers) need a property signature that is a string or None. "
                "No @property-decorated methods allowed."
            )

        # Class creation also registers it automatically (if the class is not abstract).
        if TypeSerializer._decide_register(cls, register_meta):
            _SerializableSerializer.create_derived_class(cls)
