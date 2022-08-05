from xerializer import TypeSerializer
import uuid


class EnumSerializer(TypeSerializer):
    """
    Abstract enum.Enum serializer

    Concretizations of this class should be done using :func:`register_enum`.
    """

    def as_serializable(self, obj):
        return {"name": obj.name}

    def from_serializable(self, name):
        return getattr(self.handled_type, name)


def register_enum(base_enum):
    """
    Registers an existing enumeration for xerialization.

    :param base_enum: The base enumeration class.
    """

    globals()[base_enum.__qualname__] = type(
        base_enum.__name__ + "_" + uuid.uuid4().hex[:20],
        (EnumSerializer,),
        {"__module__": __name__, "handled_type": base_enum},
    )
