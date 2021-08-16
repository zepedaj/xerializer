r"""
E\ **X**\ tensible S\ **erializer**
"""


#
from .builtin_plugins import Literal
from .abstract_type_serializer import TypeSerializer, Serializable
from .serializer import Serializer
from ._registered import register_custom_serializer, get_registered_serializers, clear_registered_serializers

__all__ = ['Serializer', 'Literal', 'TypeSerializer', 'Serializable',
           'register_custom_serializer', 'get_registered_serializers',
           'clear_registered_serializers']
