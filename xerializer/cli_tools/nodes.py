from dataclasses import dataclass, field
import abc
from threading import RLock
from .ast_parser import Parser
from typing import Any, Set, Dict, Tuple, Callable, Optional, List
from enum import Enum, auto


def _kw_only():
    """
    Provides kw-only functionality for versions ``dataclasses.field`` that do not support it.

    .. TODO:: Use dataclass's ``kw_only`` support (`https://stackoverflow.com/a/49911616`).
    """
    raise Exception("Required keyword missing")


class FLAGS(Enum):
    HIDDEN = auto()


@dataclass
class Node:
    """
    Base node used to represent contants, containers, keys and values.
    """
    flags: Set[FLAGS] = field(default_factory=set)
    parent: Optional['Node'] = None
    """
    The parent node.
    """
    parser: Parser = field(default_factory=_kw_only)
    """
    The Python parser used to resolve node types, node modifiers and node content.
    """

    @abc.abstractmethod
    def resolve(self):
        """
        Computes and returns the node's value.
        """

    # @property
    # def branch(self):
    #     """
    #     Returns the list of nodes from the root (inclusive) down to this node (inclusive).
    #     """
    #     branch = [self]
    #     while (parent := branch[0].parent) is not None:
    #         branch.insert(0, parent)
    #     return branch

    # def root(self):
    #     """
    #     Returns the root node.
    #     """
    #     return self.branch[0]

    # @property
    # def qual_name(self):
    #     """
    #     Returns the fully-qualified node name relative to the root node.
    #     """
    #     return '.'.join(x.name for x in self.branch())


@dataclass
class ValueNode(Node):
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

    def resolve(self) -> Any:
        if isinstance(self.input_content, str):
            if self.input_content[0] == '$':
                return self.parser.eval(self.input_content[1:])
            elif self.input_content[0] == '\\':
                return self.input_content[1:]
            else:
                return self.input_content
        else:
            return self.input_content
