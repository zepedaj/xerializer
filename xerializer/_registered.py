from pglib.validation import checked_get_unique
from typing import Union, List


_THIRD_PARTY_PLUGINS = []
"""
Contains list of external supported types. External modules register their types by appending to this dictionary using :meth:`register_custom_serializer`.

There is no need to manually register modules. All classes that derive from :class:`~xerializer.abstract_type_serializer.TypeSerializer` and `~xerializer.abstract_type_serializer.Serializable` are automatically registered.
"""


def register_custom_serializer(
        type_serializer):
    """
    :param type_serializer: The type serializer to register. Should derive from :class:`~pglib2.serializer2.abstract_type_serializer.Serializer`
    :param as_serializable: If ``True`` and ``type_serializer.as_serializable != None``, register this type serializer for serialization.
    :param from_serializable: If ``True`` and ``type_serializer.from_serializable != None``, register this type serializer for deserialization.
    """
    _THIRD_PARTY_PLUGINS.append(type_serializer)


def create_signature_aliases(
        signature: str,
        aliases: Union[List[str], str]):
    """
    Creates a signature aliases for deserialization functionality. Alternatively, aliases can be appended directly to :attr:`TypeSerializer.aliases`. This function can only alias registered third-party plugins.

    :param signature: The signature of the type already registered.
    :param alias: The new signature (or list of signatures) to associate to the serializer. The original signature will still be valid.
    """
    if not signature or not isinstance(signature, str):
        raise Exception(f'Invalid input type {type(signature)} for parameter `signature`.')
    type_serializer = checked_get_unique(list(filter(
        lambda x: x.signature == signature, _THIRD_PARTY_PLUGINS)))
    aliases = [aliases] if isinstance(aliases, str) else aliases
    for _al in aliases:
        type_serializer.aliases.append(_al)


# def get_registered_serializers(as_types=True):
#     getter = type if as_types else lambda x: x
#     return {'as_serializable': [getter(x) for x in _REGISTERED_AS_SERIALIZABLE_PLUGINS],
#             'from_serializable': [getter(x) for x in _REGISTERED_FROM_SERIALIZABLE_PLUGINS]}


# def clear_registered_serializers():
#     _REGISTERED_AS_SERIALIZABLE_PLUGINS.clear()
#     _REGISTERED_FROM_SERIALIZABLE_PLUGINS.clear()
