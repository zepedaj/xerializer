from dataclasses import dataclass, field
from typing import Tuple, Callable
import re
from .parser import pxs, AutonamePattern

from .nodes import Node, _kw_only


@dataclass
class KeyNode(Node):
    """
    Key nodes consist of **(1)** a :attr:`name` attribute of type ``str`` containing a valid Python variable name and **(2)** a child :attr:`value` attribute of type :class:`ValueNode'.

    Key nodes can be initialized from a raw string in a ``<name>:<type>:<modifiers>`` format, where

    * **name** will be used to set :attr:`KeyNode.name`
    * **type** is a either a valid parser context type, xerializer-recognized string signatures, or tuple of these
    * **modifiers** is a callable or tuple of callables

    """

    _name: str = field(default_factory=_kw_only)
    _content: 'Node' = field(default_factory=_kw_only)
    """
    Can be anything except another :class:`KeyNode`.
    """
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

    def __init__(self, raw_key: str, content: Node, parser, **kwargs):
        """
        :param raw_key: A string in the form 'name[:<optional type>[:<optional modifier list>]]'.
        """

        # Extract data from raw key.
        components = self._parse_raw_key(raw_key)
        if 'type' in components:
            components['type'] = parser.parse(components['type'])
        if 'modifiers' in components:
            components['modifiers'] = parser.parse(components['modifiers'])

        # Init fields
        super().__init__(
            _name=components.pop['name'],
            content=content, parser=parser, **kwargs, **components)

    @property
    def name(self): return self._name

    @name.setter
    def name(self):
        """
        Changing the name changes the __hash__ output, which will break the dictionary container set-based storage.
        """
        raise Exception('The name of KeyNode objects cannot be changed.')

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        with self.lock:
            content.parent = self
            self._content = content

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
