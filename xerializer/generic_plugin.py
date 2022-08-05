from xerializer import TypeSerializer
import abc
import uuid

DEFAULT_SOURCE_CLASS_KEY = "source_class"
"""
Default name of source class key.
"""


class Generic:
    """
    Classes serialized as generic using :meth:`register_generic` will have their objects serialized as objects of this class. The class offers no functionality and rather only mimicks the attribute interface of the handled object. The deserialized class will by default include an attribute (with default name :attr:`DEFAULT_SOURCE_KEY`) pointing to the original class, unless this functionality is desable by specifying the attribute name as ``None``.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class GenericSerializer(TypeSerializer):
    """
    Serializes any object by serializing only the attributes in :meth:`__dict__`, assuming these are xerializable. Deserialized objects will be of type :class:`Generic` and contain the same attributes, but the link to the original class will be lost.

    Concretizations of this class should be done using :func:`register_generic`.
    """

    @property
    @abc.abstractmethod
    def source_class_key():
        """
        Name for attribute used to store the source class. Skipped if set to None.
        """

    signature = "generic"
    excluded_attribs = None
    """
    Exclude these attributes.
    """
    included_attribs = None
    """
    Include these attributes - usefull for class attributes that are not included by default.
    """
    only_attribs = None
    """
    Overrides ``included_attribs`` and ``excluded_attribs`` - only the attributes in this iterable will be included.
    """

    def as_serializable(self, obj):
        if self.only_attribs:
            attribs = self.only_attribs
        else:
            attribs = set(list(obj.__dict__) + (self.included_attribs or [])) - set(
                self.excluded_attribs or []
            )
        out = {}
        if self.source_class_key is not None:
            out = {self.source_class_key: type(obj)}
        out.update({key: getattr(obj, key) for key in attribs})
        return out

    def from_serializable(self, **kwargs):
        return Generic(**kwargs)


def register_generic(
    cls,
    only=None,
    include=None,
    exclude=None,
    source_class_key=DEFAULT_SOURCE_CLASS_KEY,
):
    """
    Creates a concrete instance of :class:`GenericSerializer` associated to the specified input class

    :param cls: Input class to make serializable as a :class:`Generic` object.
    """

    globals()[cls.__qualname__] = type(
        cls.__name__ + "_" + uuid.uuid4().hex[:20],
        (GenericSerializer,),
        {
            "__module__": __name__,
            "handled_type": cls,
            "only_attribs": only,
            "included_attribs": include,
            "excluded_attribs": exclude,
            "source_class_key": source_class_key,
        },
    )
