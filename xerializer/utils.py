from .serializer import Serializer


class AsPickleable:
    """
    Takes a serializable object and returns a new object that pickles using xerializer serialization, and unpickles to the deserialized object.

    The pickled object will include the original serializer.

    .. warning:: This class relies on accepts an input |Serializer| that is itself serialized using the |Serializer| in class attribute :attr:`bootstrap_serializer`.

    .. warning:: The standard pickle safety warnings apply.

    """

    bootstrap_serializer = Serializer()
    """
    Used to serialize the input serializer.
    """

    def __init__(self, obj, serializer: Serializer = None):
        self.serialized_serializer = self.bootstrap_serializer.serialize(
            serializer := (serializer or Serializer()))
        self.serialized_obj = serializer.serialize(obj)

    @classmethod
    def _restore(cls, serialized_obj, serialized_serializer):
        serializer = cls.bootstrap_serializer.deserialize(serialized_serializer)
        obj = serializer.deserialize(serialized_obj)
        return obj

    def __reduce__(self):
        out = self._restore, (self.serialized_obj, self.serialized_serializer)
        return out
