_REGISTERED_AS_SERIALIZABLE_PLUGINS = []
_REGISTERED_FROM_SERIALIZABLE_PLUGINS = []
"""
Contains list of external supported types. External modules register their types by appending to these dictionaries using :meth:`register_custom_serializer`.

By default, there is no need to manually register modules. All classes that derive from :class:`~xerializer.abstract_type_serializer.TypeSerializer` and `~xerializer.abstract_type_serializer.Serializable` are automatically registered.
"""


def register_custom_serializer(
        type_serializer,
        as_serializable=True,
        from_serializable=True):
    """
    :param type_serializer: The type serializer to register. Should derive from :class:`~pglib2.serializer2.abstract_type_serializer.Serializer`
    :param as_serializable: If ``True`` and ``type_serializer.as_serializable != None``, register this type serializer for serialization.
    :param from_serializable: If ``True`` and ``type_serializer.from_serializable != None``, register this type serializer for deserialization.
    """
    if as_serializable and type_serializer.as_serializable is not None:
        _REGISTERED_AS_SERIALIZABLE_PLUGINS.append(type_serializer)
    if from_serializable and type_serializer.from_serializable is not None:
        _REGISTERED_FROM_SERIALIZABLE_PLUGINS.append(type_serializer)
