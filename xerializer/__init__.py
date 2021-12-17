r"""
E\ **X**\ tensible S\ **erializer**
"""


#
from .builtin_plugins import Literal
from .abstract_type_serializer import TypeSerializer, Serializable, default_signature
from .serializer import Serializer
from ._registered import (register_custom_serializer, create_signature_aliases)
from .decorator import serializable
from .cli_builder import hydra_cli

__all__ = ['Serializer', 'Literal', 'TypeSerializer', 'Serializable', 'serializable',
           'default_signature', 'register_custom_serializer', 'create_signature_aliases',
           'hydra_cli']
