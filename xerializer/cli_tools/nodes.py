"""
"""
from dataclasses import dataclass, field
from .modifiers import parent
import numpy as np
import abc
from .ast_parser import Parser
from typing import Any, Set, Optional
from enum import Enum, auto
from . import varnames
import re


def _kw_only():
    """
    Provides kw-only functionality for versions ``dataclasses.field`` that do not support it.

    .. TODO:: Use dataclass's ``kw_only`` support (`https://stackoverflow.com/a/49911616`).
    """
    raise Exception("Required keyword missing")


class FLAGS(Enum):
    HIDDEN = auto()


# Add sphinx replacements.
__doc__ += f"\n{varnames.SPHINX_DEFS}"


@dataclass
class Node(abc.ABC):
    """
    Base node used to represent contants, containers, keys and values.
    """
    flags: Set[FLAGS] = field(default_factory=set)
    parent: Optional['Node'] = field(default=None, init=False)
    """
    The parent node. This field is handled by container nodes and should not be set explicitly.
    """

    @abc.abstractmethod
    def resolve(self):
        """
        Computes and returns the node's value.
        """

    _REF_STR_COMPONENT_PATTERN = r'((?P<parents>\.+)|(?P<index>(0|[1-9]\d*))|(?P<key>[a-zA-Z+]\w*))'
    _FULL_REF_STR_PATTERN = _REF_STR_COMPONENT_PATTERN + '+'
    # Compile the patterns.
    _REF_STR_COMPONENT_PATTERN = re.compile(_REF_STR_COMPONENT_PATTERN)
    _FULL_REF_STR_PATTERN = re.compile(_FULL_REF_STR_PATTERN)

    def __call__(self, ref: str = '.', calling_node=None):
        """
        Retrieves the resolved value of a dependent node relative to ``self`` using a dot-separated reference string.

        The string can contain a sequence of dot-separated keys or integer. A sequence of ``N`` contiguous dots refers to the ``N-1``-th parent node. Omitting the reference string will resolve the entire node tree

        .. rubric:: Examples

        .. code-block::

          #
          raw_data = {'my_key0':[0,1,2], 'my_key1':[4,5,6]}
          root = AlphaConf(raw_data).node_tree # Retrieves the root node.

          # Ref string syntax
          assert root() == raw_data
          assert root('my_key0.1') == 0
          assert root('my_key0..my_key1.2') == 6
          assert root('my_key0.0...') == raw_data

          # Alternate syntax with __getitem__ on container nodes
          # - retrieve the node with a sequence of __getitem__ calls
          # and then resolve the node with a __call__ call.
          assert root['my_key0'][1]() == 0
          assert root['my_key0']['my_key1'][2]() == 6
          assert parent(root['my_key0'][0], 2)() == raw_data

        :param ref: A string of dot-separated keys, indices or empty strings.

        """

        # Check full syntax matches.
        if not re.fullmatch(self._FULL_REF_STR_PATTERN, ref):
            raise Exception(f'Invalid reference string `{ref}`.')

        # Apply ref components.
        node = self
        for _key_match in re.finditer(self._REF_STR_COMPONENT_PATTERN, ref):
            if (ref := _key_match['parents']) is not None:
                node = parent(node, len(ref)-1)
            elif (ref := _key_match['key']) is not None:
                node = node[ref]
            elif (ref := _key_match['index']) is not None:
                node = node[int(ref)]
            else:
                raise Exception('Unexpected case!')

        # Resolve the node
        return node.resolve()


@dataclass
class ParsedNode(Node):
    """
    A node that has content that needs to be Python-parsed.
    """
    parser: Parser = field(default_factory=_kw_only)
    """
    The Python parser used to resolve node types, node modifiers and node content.
    """

    def eval(self, py_expr: str):
        """
        Evaluates the python expression ``py_expr``, adding ``self`` as variable |CURRENT_NODE_VAR_NAME| in the parser evaluation context.
        """
        return self.parser.eval(py_expr, {varnames.CURRENT_NODE_VAR_NAME: self})


@dataclass
class ValueNode(ParsedNode):
    """
    Value nodes are nodes that contain children-less content. The content of value nodes is obtained by resolving the input content.

    The way in which the resolution operates depends on the input content. Input contents that are not strings are passed on without modification.

    For input contents that are strings, the node's resolved content will depend on its first character:

    1. The string starts with `'$'`: the remainder of the string will be evaluated as a safe python expression returning the resolved content.
    2. The string starts with `'\'`: that character will be stripped and the remainder used as the resolved content.
    3. For any other character, the string itself will be the resolved content.
    """

    # '$1 + 2' -> 3
    # '\$1 + 2' -> '$1 + 2'
    # '\\$1 + 2' -> '\$1 + 2'
    # '\\\$fxn(1) + 2' -> '\\$fxn(1) + 2'
    # '1 + 2' -> '1 + 2'

    raw_value: str = field(default_factory=_kw_only)

    def __init__(self, raw_value, parser, **kwargs):
        self.raw_value = raw_value
        super().__init__(parser=parser, **kwargs)

    def resolve(self) -> Any:
        if isinstance(self.raw_value, str):
            if self.raw_value[0] == '$':
                return self.eval(self.raw_value[1:])
            elif self.raw_value[0] == '\\':
                return self.raw_value[1:]
            else:
                return self.raw_value
        else:
            return self.raw_value
