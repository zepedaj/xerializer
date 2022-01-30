from dataclasses import dataclass, field
import builtins
from .ast_parser import Parser, BUILTIN_SCALAR_TYPES
from typing import Any, Set, Dict, Tuple, Callable
from enum import Enum, auto
import re
from .parser import pxs, AutonamePattern


def _kw_only():
    """
    Provides kw-only functionality for versions ``dataclasses.field`` that do not support it.
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


@dataclass
class ContentNode(Node):
    """
    Contains magic methods for all ``DEFAULT_BUILTIN_TYPES`` that cast the node's content attribute.
    """
    content: Any = field(default_factory=_kw_only)

    def as_type(self, target_type) -> 'ContentNode':
        """
        Casts content to the target type and returns self.
        """
        self.content = target_type(self.content)
        return self


# Add type magic methods to ContentNode
for _target_type in BUILTIN_SCALAR_TYPES:
    setattr(ContentNode, f'__{_target_type}__',
            (lambda self, target_type=_target_type:
             self.as_type(getattr(builtins, _target_type))))


@dataclass
class DictContainer(ContentNode):
    content: Dict[Node, Node] = field(default_factory=_kw_only)


@dataclass
class KeyNode(Node):
    """
    Key nodes consist of **(1)** a :attr:`name` attribute of type ``str`` containing a valid Python variable name and **(2)** a child :attr:`value` attribute of type :class:`ValueNode'.

    Key nodes can be initialized from a raw string in a ``<name>:<type>:<modifiers>`` format, where

    * **name** will be used to set :attr:`KeyNode.name`
    * **type** is a either a valid parser context type, xerializer-recognized string signatures, or tuple of these
    * **modifiers** is a callable or tuple of callables

    """

    name: str = field(default_factory=_kw_only)
    value: 'ValueNode' = field(default_factory=_kw_only)
    modifiers: Tuple[Callable] = tuple()

    # Matches a single type/signature
    SINGLE_TYPE_PATTERN = AutonamePattern(
        '('
        # Matches a type
        '{VARNAME}' '|'
        # Matches quoted signatures (with optional colon separator)
        r'(?P<q>\'|\"){NS_VARNAME}((?P<colon>:)({VARNAME}))?(?P=q)'
        ')', vars(pxs))
    """
    Expected type or xerializer signature string representation format. Signatures need to be strings.
    """

    # Matches a single type/signature or a tuple of mixed types/signatures.
    # Tuples may be optionally parentheses-enclosed.
    TYPE_PATTERN = AutonamePattern(
        r'(?P<paren>\(\s*)?'
        r'{SINGLE_TYPE_PATTERN}(\s*,\s*{SINGLE_TYPE_PATTERN})*'
        r'(?(paren)\s*\))',
        vars())
    """
    Matches a single type/signature or a sequence of types/signatures.
    """

    RAW_KEY_PATTERN = re.compile(
        f'(?P<name>{pxs.VARNAME})'
        r'('
        f'\\s*:\\s*(?P<type>({TYPE_PATTERN}))?'
        # Modifiers could be better checked. Should be a callable or tuple.
        r'(\s*:\s*(?P<modifiers>(.*)))?'
        r')?\s*',
    )

    """
    Valid described-key pattern.
    """

    def __init__(self, raw_key: str):
        """
        :param raw_key: A string in the form 'name[:<optional type>[:<optional modifier list>]]'.
        """

    def __hash__(self):
        return self.name

    @classmethod
    def _parse_raw_key(cls, raw_key):
        """
        Returns a dict with 'name', 'type' and 'modifiers'. The content of 'type' and 'modifiers' will be None if unavailable.
        """
        if not (match := re.fullmatch(cls.RAW_KEY_PATTERN, raw_key)):
            # TODO: Add the file, if available, to the error message.
            raise Exception(f'Invalid described key syntax `{raw_key}`.')
        else:
            out = {key: match[key] for key in ['name', 'type', 'modifiers']}
            if out['type'] and out['type'][0] in '\'"':
                # Strip quotes
                out['type'] = out['type'][1:-1]
            return out


class _UNRESOLVED:
    pass


@ dataclass
class ValueNode(ContentNode):
    """
    The content of value nodes is obtained by resolving the input content.

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

    input_content: str = field(default_factory=_kw_only)
    _resolved_content: Any = _UNRESOLVED
    parser: Parser = Parser()
    _dependency: Node = None
    """
    Content that cannot yet be resolved will have this field set to the blocking node.
    """

    @ property
    def content(self):
        if self._resolved_content is _UNRESOLVED:
            self._resolved_content = self.resolve()
        return self._resoved_content

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
