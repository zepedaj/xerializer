"""
.. |raw key format| replace:: ``'name[:<types>[:<modifiers>]]'``
"""

from dataclasses import dataclass, field
from contextlib import contextmanager, nullcontext
from typing import Tuple, Callable, Union, Dict, Optional
import re
from .parser import pxs, AutonamePattern
from .containers import Container
from .nodes import Node, ParsedNode, _kw_only
from threading import RLock


class _RawKeyPatterns:
    """
    Contains regular expressions used to extract key type and modifier decorations from a string key.

    String keys have the format |raw key format|.
    """

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
        f'\\s*:\\s*(?P<types>({TYPE_PATTERN}))?'
        # Modifiers could be better checked. Should be a callable or tuple.
        r'(\s*:\s*(?P<modifiers>(.*)))?'
        r')?\s*',
    )
    """
    Valid described-key pattern.
    """


class KeyNode(ParsedNode):
    """
    Key nodes represent a Python dictionary entry and as such, they must always be used as :class:`DictContainer` children. Key nodes have

    1. a :attr:`name` attribute of type ``str`` containing a valid Python variable name and
    2. a :attr:`value` attribute of type :class:`ValueNode`, :class:`DictNode` or :class:`ListNode`.


    .. _raw string:
    .. rubric:: Initialization from raw string

    Key nodes can be initialized from a raw string in the format |raw key format|, where

    * **name** will be used to set :attr:`KeyNode.name` and must be a valid variable name;
    * **types** is a either a valid type in the parser's context, an xerializer-recognized string signature, or a tuple of these; and
    * **modifiers** is a callable or tuple of callables that take a node as an argument an modify it and potentially replace it.

    Both **types** and **modifiers** must be valid python statements.

    .. _key node life cycle:
    .. rubric:: Key node life cycle

    Key node modifiers are applied at the end of node initialization. Type checking is applied at the end of node resolution. Typically, this happens in the following order:



    1. Modifiers are applied sequentially to ``self`` at the end of initialization. A modifier can optionally return a new node, in which case subsequent modifiers will be applied to this new node instead of ``self``. This functionality is handy when, e.g., a modifier replaces a node by a new node. This process is illustrated by the following code snippet that executes at the end of node initialization:

      .. code-block::

        node = self
        for modifier in modifiers:
          node = modifier(node) or node

    2. When the node is resolved by a call to :meth:`resolve`, the node checks that the type of the resolved value is one of the valid types, if any where supplied, and raises a :class:`TypeError` otherwise.

    """

    _name: str = field(default_factory=_kw_only)
    """
    Changing the name must go through the name.setter() call.
    """
    value: 'Node' = field(default_factory=_kw_only)
    """
    Can be any :class:`Node`-derived type except another :class:`KeyNode`.
    """
    modifiers: Tuple[Callable[[Node], Optional[Node]]] = tuple()
    """
    Tuple of modifiers to apply sequentially to ``self``. See :ref:`key node life cycle`.
    """
    types: Tuple[Union[str, type]] = tuple()
    """
    Tuple of expected resolved types.
    """
    _lock: RLock = None

    def __init__(self, raw_key: str, value: Node, parser, **kwargs):
        """
        Initializes the node, setting the parent of value as ``self``.

        :param raw_key: A string in the form |raw key format| (see :ref:`raw string`).
        :param value: The value node. The parent of this node will be set to ``self`` during initialization.
        :param kwargs: This object is a dataclass, all class attributes (including those inherited) can be used as keyword args.
        """

        # Extract data from raw key.
        components = self._parse_raw_key(raw_key)
        self._name = components['name']
        if 'type' in components:
            types = parser.eval(components['types']) or tuple()
            self.types = types if isinstance(types, tuple) else (types,)
        if 'modifiers' in components:
            modifiers = parser.eval(components['modifiers']) or tuple()
            self.modifiers = modifiers if isinstance(modifiers, tuple) else (modifiers,)

        #
        value.parent = self
        self.value = value
        self.lock = RLock()
        super().__init__(self, parser=parser, **kwargs)

        # Apply modifiers.
        node = self
        for modifier in self.modifiers:
            node = modifier(node) or node

    @contextmanager
    def lock(self):
        """
        Locks the node and, if the node is bound, the parent.
        """
        with self.lock:
            if self.parent:
                with self.parent.lock:
                    yield
            else:
                yield

    def __str__(self):
        return f"KeyNode<'{self.name}'>"

    @property
    def name(self): return self._name

    @name.setter
    def name(self, new_name):
        """
        KeyNode names can only be changed if the ``KeyNode``'s parent container is ``None``.
        """
        with self.lock:
            if self.parent is not None:
                raise Exception(f'Remove `{self}` from parent container before re-naming.')
            else:
                self._name = new_name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, val):
        """
        Compares to strings or other :class:`KeyNode`s based on the key. Together with :meth:`__hash__`, this method enables
        using :class:`KeyNode`s as keys in :attr:`DictContainer.children` that will behave as string keys.
        """
        if isinstance(val, str):
            return val == self.name
        elif isinstance(val, KeyNode):
            return val.name == self.name

    @classmethod
    def _parse_raw_key(cls, raw_key):
        """
        Returns a dict with 'name', 'types' and 'modifiers'. The content of 'type' and 'modifiers' will be None if unavailable.
        """
        if not (match := re.fullmatch(_RawKeyPatterns.RAW_KEY_PATTERN, raw_key)):
            # TODO: Add the file, if available, to the error message.
            raise Exception(f'Invalid described key syntax `{raw_key}`.')
        else:
            out = {key: match[key] for key in ['name', 'types', 'modifiers']}
            return out

    def resolve(self):
        """
        Returns the resolved name and value as a tuple.
        """
        #
        with self.lock:
            name = self.name
            value = self.value.resolve()
            #
            if self.types and not isinstance(value, self.types):
                raise TypeError(f'Invalid type {type(value)}. Expected one of {self.types}.')
            return name, value


@dataclass
class DictContainer(Container):
    """
    Contains a dictionary node. Adding and removing entries to this dictinoary should be done entirely using :meth:`add` and :meth:`remove` to ensure correct handling of parent/child relationships.
    """

    children: Dict[Node, Node] = None
    # Both key and value will be the same KeyNode, ensuring a single source for the
    # node name.
    #
    # This approach will also behave in a way similar to dictionaries when inserting nodes
    # with the same name. Node indexing can be done using a key that is the KeyNode or the
    # node name as a string,  a behavior enable by the KeyNodes.__eq__ implementation.
    #
    # Using a set seemed like a more natural solution, but I was unable to
    # retrieve an object from a set given a matching key (I tried `node_set.intersection(key)`,
    # and `{key}.intersection(node_set)` )
    #
    # WARNING: Changing the name of a key node without taking care that
    # that node is not a part of a dictionary where another KeyNode exists with the
    # same name will result in unexpected behavior.

    def __init__(self, **kwargs):
        self.children = {}
        super().__init__(**kwargs)

    def add(self, node: KeyNode):
        """
        Adds the node to the container or replaces the node with the same name if one exists.
        The node's parent is set to ``self``.
        """
        with self.lock, node.lock:
            if node.parent is not None:
                raise Exception('Attempted to add a node that already has a parent.')
            # Remove node of same name, if it exists.
            self.remove(node, safe=True)
            # Add the new node.
            node.parent = self
            self.children[node] = node

    def remove(self, node: Union[KeyNode, str], safe=False) -> KeyNode:
        """
        Removes the child node with the same name as ``node`` from the container.

        The removed node's parent is set to ``None`` and the node is returned.

        :param node: The name or node whose name will serve as a key.
        :param safe: Whether to ignore non-existing keys.

        .. warning:: The remove node is only guaranteed to match the input node in name.
        """
        with self.lock, (nullcontext(None) if isinstance(node, str) else node.lock):
            if popped_node := self.children.pop(node, *((None,) if safe else tuple())):
                popped_node.parent = None
                return popped_node

    def resolve(self):
        """
        Returns the resolved dictionary.
        """
        return dict(child.resolve() for child in self.children.values())

    def __getitem__(self, key: str):
        """
        Returns the resolved value for the specified key.
        """
        name, value = self.children[key].resolve()
        return value
