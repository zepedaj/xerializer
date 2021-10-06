r"""
E\ **X**\ tensible S\ **erializer**
"""


#
from .builtin_plugins import Literal
from .abstract_type_serializer import TypeSerializer, Serializable, default_signature
from .serializer import Serializer
from ._registered import (register_custom_serializer, get_registered_serializers,
                          clear_registered_serializers, create_signature_aliases)
from .decorator import serializable

__all__ = ['Serializer', 'Literal', 'TypeSerializer', 'Serializable', 'serializable',
           'default_signature', 'register_custom_serializer', 'get_registered_serializers',
           'clear_registered_serializers', 'create_signature_aliases']
