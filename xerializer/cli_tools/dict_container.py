"""
.. |raw key format| replace:: ``'name[:<types>[:<modifiers>]]'``
"""

from contextlib import contextmanager, nullcontext
from typing import Union, Dict, Optional
import re
from .parser import pxs, AutonamePattern
from .ast_parser import Parser
from .containers import Container
from .nodes import Node, ParsedNode, FLAGS
from threading import RLock
from . import exceptions


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
        f'(?P<key>{pxs.VARNAME})'
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
    Key nodes represent a Python dictionary entry and as such, they must always be used as :class:`DictContainer` children. They implement part of the :class:`Container` interface. Key nodes have

    1. a :attr:`key` attribute of type ``str`` containing a valid Python variable name and
    2. a :attr:`value` attribute of type :class:`ValueNode`, :class:`DictNode` or :class:`ListNode`.


    .. _raw string:
    .. rubric:: Initialization from raw string

    Key nodes can be initialized from a raw string in the format |raw key format|, where

    * **key** will be used to set :attr:`KeyNode.key` and must be a valid variable name;
    * **types** is either a valid type in the parser's context, an xerializer-recognized string signature, or a tuple of these; and
    * **modifiers** is a callable or tuple of callables that take a node as an argument an modify it and potentially replace it.

    Both **types** and **modifiers** must be valid python statements.

    .. _key node life cycle:
    .. rubric:: Key node life cycle

    Key node modifiers are applied by calling the node's :meth:`modify` method. Type checking is applied at the end of node resolution. Typically, this happens in the following order:


    1. Modifiers are applied sequentially to ``self``. A modifier can optionally return a new node, in which case subsequent modifiers will be applied to this new node instead of ``self``. This functionality is handy when, e.g., a modifier replaces a node by a new node. This process is illustrated by the following code snippet inside :meth:`modify`:

      .. code-block::

        node = self
        for modifier in modifiers:
          node = modifier(node) or node

    2. When the node is resolved by a call to :meth:`resolve`, the node checks that the type of the resolved value is one of the valid types, if any where supplied, and raises a :class:`TypeError` otherwise.

    """

    def __init__(self, raw_key: str, value: Node, parser: Parser, **kwargs):
        """
        Initializes the node, setting the parent of value as ``self``.

        :param raw_key: A string in the form |raw key format| (see :ref:`raw string`).
        :param value: The value node. The parent of this node will be set to ``self`` during initialization.
        :param kwargs: This object is a dataclass, all class attributes (including those inherited) can be used as keyword args.
        """

        # Extract data from raw key.
        components = self._split_raw_key(raw_key)
        self._key = components['key']
        #
        value.parent = self
        self.value = value
        self.lock = RLock()
        super().__init__(self, parser=parser, **kwargs)

        #
        self.types = self._parse_raw_key_component(components['types'])
        self.modifiers = self._parse_raw_key_component(components['modifiers'])
        self.modified = False

    @property
    def hidden(self):
        return super().hidden or FLAGS.HIDDEN in self.value.flags

    def modify(self):
        """
        This function first parses the key components (``'types'`` and ``'modifiers'``) and then applies the modifiers to the node.

        Calling this function a second time has no effect.
        """

        # Check if the modifiers have been applied.
        if self.modified:
            return

        # Parse types and modifiers.
        #self.types = self._parse_raw_key_component(self.raw_types)
        #self.modifiers = self._parse_raw_key_component(self.raw_modifiers)

        # Apply modifiers.
        node = self
        if self.modifiers:
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

    @property
    def key(self): return self._key

    @key.setter
    def key(self, new_key):
        """
        KeyNode keys can only be changed if the ``KeyNode``'s parent container is ``None``.
        """
        with self.lock:
            if self.parent is not None:
                raise Exception(f'Remove `{self}` from parent container before re-naming.')
            else:
                self._key = new_key

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, val):
        """
        Compares to strings or other :class:`KeyNode`s based on the key. Together with :meth:`__hash__`, this method enables
        using :class:`KeyNode`s as string keys in :attr:`DictContainer.children` ``__getitem__`` calls.
        """
        if isinstance(val, str):
            return val == self.key
        elif isinstance(val, KeyNode):
            return val.key == self.key

    @classmethod
    def _split_raw_key(cls, raw_key: str):
        """
        Returns a dict with sub-strings 'key', 'types' and 'modifiers'. The content of 'types' and 'modifiers' will be None if unavailable.
        """
        if not (match := re.fullmatch(_RawKeyPatterns.RAW_KEY_PATTERN, raw_key)):
            # TODO: Add the file, if available, to the error message.
            raise Exception(f'Invalid described key syntax `{raw_key}`.')
        else:
            return {key: match[key] for key in ['key', 'types', 'modifiers']}

    def _parse_raw_key_component(self, component: Optional[str]):
        """
        Evaluates the component ('types' or 'modifiers') and returns its parsed value. If this is not a tuple, it is instead returned as a single-entry tuple.
        """
        if component is None:
            return None
        component = self.eval(component) if component else tuple()
        component = component if isinstance(component, tuple) else (component,)
        return component

    def _unsafe_resolve(self):
        """
        Returns the resolved key and value as a tuple.
        """
        #
        with self.lock:
            key = self.key
            value = self.value.resolve()
            #
            if self.types and not isinstance(value, self.types):
                raise TypeError(f'Invalid type {type(value)}. Expected one of {self.types}.')
            return key, value

    def replace(self, old_value=Optional[Node], new_value: Node = None):
        """
        Replaces the value node by a new value node. 

        :param old_value: If provided, must be the current value node :attr:`value`. Use ``None`` to specify it by default. This signature is provided for consistency with the :class:`Container` signature.
        :param new_value: The new value node.
        """
        with self.lock, new_value.lock:
            old_value = old_value or self.value
            with old_value.lock:
                if old_value is not self.value:
                    raise exceptions.NotAChildOfError(old_value, self)
                old_value.parent = None
                self.value = new_value
                new_value.parent = self

    def get_child_qual_name(self, child_node):
        """
        Returns the dictionary-container-relative qualified name.

        Key nodes (respectively, their value nodes) can be accessed directly by indexing the parent :class:`DictContainer` with a ``'*'``-prefixed key (non-prefixed key) as an index. E.g., the ref string ``'*key'`` and ``'key'`` will indicate, respectively, the key node of key ``'key'`` and its value node.

        .. rubric:: Example

        .. test-code::

          from xerializer.cli_tools.tree_builder import AlphaConf

          ac = AlphaConf({'node0': {'node1': 1}})

          # Refer to the value node.
          node = ac['node0']['node1']
          assert node==ac.children['node0'].children['node1'].value
          assert node.qual_name == 'node0.node1'

          # Refer to the key node.
          node = ac['node0']['*node1']
          assert node==ac.children['node0'].children['node1']
          assert node.qual_name == 'node0.*node1'

        """

        if child_node is self.value:
            # DictContainer objects can refer to the key or value node directly.
            # See :meth:`DictContainer.__getitem__`.
            if not self.parent:
                raise Exception('Attempted to retrieve the qualified name of an unbounded KeyNode.')
            return self.parent._derive_qual_name(self.key)
        else:
            raise exceptions.NotAChildOfError(child_node, self)


class DictContainer(Container):
    """
    Contains a dictionary node. Adding and removing entries to this container should be done entirely using :meth:`add` and :meth:`remove` to ensure correct handling of parent/child relationships.
    """

    _REF_COMPONENT_PATTERN = re.compile(r'\*?[a-zA-Z_]\w*')

    children: Dict[Node, Node] = None
    # Both key and value will be the same KeyNode, ensuring a single source for the
    # node key.
    #
    # This approach will also behave in a way similar to dictionaries when inserting nodes
    # with the same key. Node indexing can be done using a key that is the KeyNode or the
    # node key as a string,  a behavior enable by the KeyNodes.__eq__ implementation.
    #
    # Using a set seemed like a more natural solution, but I was unable to
    # retrieve an object from a set given a matching key (I tried `node_set.intersection(key)`,
    # and `{key}.intersection(node_set)` )
    #
    # WARNING: Changing the key of a key node without taking care that
    # that node is not a part of a dictionary where another KeyNode exists with the
    # same key will result in unexpected behavior.

    def __init__(self, **kwargs):
        self.children = {}
        super().__init__(**kwargs)

    def add(self, node: KeyNode):
        """
        Adds the node to the container or replaces the node with the same key if one exists.
        The node's parent is set to ``self``.
        """
        with self.lock, node.lock:
            if node.parent is not None:
                raise Exception('Attempted to add a node that already has a parent.')
            # Remove node of same key, if it exists.
            self.remove(node, safe=True)
            # Add the new node.
            node.parent = self
            self.children[node] = node

    def remove(self, node: Union[KeyNode, str], safe=False) -> KeyNode:
        """
        Removes the child node with the same key as ``node`` from the container.

        The removed node's parent is set to ``None`` and the node is returned.

        :param node: The key or node whose key will serve as a key.
        :param safe: Whether to ignore non-existing keys.

        .. warning:: The removed node is only guaranteed to match the input node in key.
        """
        with self.lock, (nullcontext(None) if isinstance(node, str) else node.lock):
            if popped_node := self.children.pop(node, *((None,) if safe else tuple())):
                popped_node.parent = None
                return popped_node

    def replace(self, old_node: Union[str, Node], new_node: Node):
        """
        Removes the old node and adds the new node. Both nodes do not need to have the same hash key.
        """

        old_node = self[old_node]
        with self.lock, new_node.lock, old_node.lock:
            self.remove(old_node)
            self.add(new_node)

    def _unsafe_resolve(self):
        """
        Returns the resolved dictionary.
        """
        return dict(child.resolve() for child in self.children.values() if not child.hidden)

    def __getitem__(self, key: str):
        """
        Returns the resolved value for the specified key.

        By default, the returned node is the :class:`ValueNode` child of the referred :class:`KeyNode`.

        To instead the obtain the :class:`KeyNode`, prepended the input key string with a ``'*'`` character.
        """
        if not isinstance(key, str):
            raise Exception(f'Expected a string key but got `{key}`.')
        if key[:1] == '*':
            return self.children[key[1:]]
        else:
            return self.children[key].value

    def get_child_qual_name(self, node: KeyNode):
        """
        Prepends a ``'*'`` character to the input key node's key before building the qualified name. See :meth:`__getitem__`.
        """

        for child_node in self.children:
            if node is child_node:
                return self._derive_qual_name(f'*{node.key}')

        raise exceptions.NotAChildOfError(child_node, self)

    def _node_from_ref_component(self, ref_component: str):
        if re.fullmatch(self._REF_COMPONENT_PATTERN, ref_component):
            return self[ref_component]
        else:
            return super()._node_from_ref_component(ref_component)
