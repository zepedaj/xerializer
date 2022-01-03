from xerializer import TypeSerializer
import uuid


class Generic:
    """
    Classes serialized as generic using :meth:`register_generic` will have their objects serialized as objects of this class. The class offers no functionality and rather only mimicks the attribute interface of the handled object.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _GenericSerializer(TypeSerializer):
    """
    Serializes any object by serializing only the attributes in :meth:`__dict__`, assuming these are xerializable. Deserialized objects will be of type :class:`Generic` and contain the same attributes, but the link to the original class will be lost.
    """

    signature = 'generic'
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
            attribs = (
                set(list(obj.__dict__) + (self.included_attribs or [])) -
                set(self.excluded_attribs or []))
        return {key: getattr(obj, key) for key in attribs}

    def from_serializable(self, **kwargs):
        return Generic(**kwargs)


def register_generic(cls, only=None, include=None, exclude=None):

    globals()[cls.__qualname__] = type(
        cls.__name__ + '_' + uuid.uuid4().hex[:20],
        (_GenericSerializer,),
        {
            '__module__': __name__,
            'handled_type': cls,
            'only_attribs': only,
            'included_attribs': include,
            'excluded_attribs': exclude,
        }
    )
