"""
"""
from dataclasses import dataclass, field
import abc
from .ast_parser import Parser
from typing import Any, Set, Optional
from enum import Enum, auto
from . import varnames


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
