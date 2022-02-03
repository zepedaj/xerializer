"""
"""
from dataclasses import dataclass, field
from .modifiers import parent
import abc
from .ast_parser import Parser
from typing import Any, Set, Optional, List
from enum import Enum, auto
from . import varnames
import re
from .resolving_node import ResolvingNode


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
    Base node used to represent contants, containers, keys and values. All nodes need to either be the root node or part of a :class:`Container`.
    """
    flags: Set[FLAGS] = field(default_factory=set)
    parent: Optional['Node'] = field(default=None, init=False)
    """
    The parent node. This field is handled by container nodes and should not be set explicitly.
    """
    dependencies: List['Node'] = field(default_factory=list)
    """
    The set of nodes that the current node depends on for resolution.
    """

    def __str__(self):
        return f"{type(self).__name__}<'{self.qual_name}'>"

    def __repr__(self):
        return str(self)

    def resolve(self):
        """
        Computes and returns the node's value, checking for cyclical references and generating meaningful error messages if these are detected.
        """

        # Set up marker variable to track node dependencies.
        __resolving_node__ = ResolvingNode.find()
        __resolving_node__.add_dependency(self)  # Checks for reference cycles.
        __resolving_node__ = ResolvingNode(self)

        return self._unsafe_resolve()

    @abc.abstractmethod
    def _unsafe_resolve(self):
        """
        Children classes need to implement this method and not the public method :meth:`resolve`, which wraps this method. As a rule of thumb, this method should never be called directly.
        Any node resolutions done inside this method should instead call method :meth:`resolve`.
        """

    _REF_STR_COMPONENT_PATTERN = r'((?P<parents>\.+)|(?P<index>(0|[1-9]\d*))|(?P<key>\*?[a-zA-Z+]\w*))'
    _FULL_REF_STR_PATTERN = _REF_STR_COMPONENT_PATTERN + '+'
    # Compile the patterns.
    _REF_STR_COMPONENT_PATTERN = re.compile(_REF_STR_COMPONENT_PATTERN)
    _FULL_REF_STR_PATTERN = re.compile(_FULL_REF_STR_PATTERN)

    def node_from_ref(self, ref: str = ''):
        """
        Returns the node indicated by the input reference string (a.k.a. "ref string"). Ref strings have the same syntax as :attr:`qualified names<qual_name>` but are interpreted relative to ``self`` rather than ``root``.

        When called from the root node, this method inverts a qualified name, returning the corresponding node.

        Similar to :attr:`qual_name`s, ref strings can contain a sequence of dot-separated keys or integer. An empty ref string will refer to ``self``, and starred keys will reffer to a dictionary container's key node rather than its value node. In addition to this, ref strings can use a sequence of ``N`` contiguous dots to refer to the ``N-1``-th parent node. 

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

        return node

    def __call__(self, ref: str = '.', calling_node=None):
        """
        Retrieves the node with the specified reference string relative to ``self`` and resolves it.
        """
        node = self.node_from_ref(ref)
        return node.resolve()

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
    #         Returns the root node.
    #         """
    #     return self.branch[0]

    @property
    def qual_name(self):
        """
        Returns the absolute node name.
        """
        return (f'{self.parent.get_child_qual_name(self)}' if self.parent else '')

    def _derive_qual_name(self, child_name: str):
        """
        Helper method to build a qualified name from a child of this node given that node's string (non-qualified) name.
        """
        return (
            f'{_qual_name}.' if (_qual_name := self.qual_name) else '') + child_name


class ParsedNode(Node):
    """
    Parsed nodes are nodes that have no children but might contain node references and python expressions that need to be resolved.

    Parsed nodes are resolved in one of four ways depending on the input value (the `raw value`):

    1. Raw values that are not strings are passed on without modification.

    For string raw values, the node's resolved content will depend on the raw value's first character:

    2. The string starts with `'$'`: the remainder of the string will be evaluated as a safe python expression returning the resolved value.
    3. The string starts with `'\'`: that character will be stripped and the remainder used as the resolved value.
    4. For any other character, the string itself will be the resolved value.
    """

    parser: Parser = field(default_factory=_kw_only)
    """
    The Python parser used to resolve node types, node modifiers and node content.
    """

    def __init__(self, raw_value, parser, **kwargs):
        self.raw_value = raw_value
        self.parser = parser
        super().__init__(**kwargs)

    def eval(self, py_expr: str):
        """
        Evaluates the python expression ``py_expr``, adding ``self`` as variable | CURRENT_NODE_VAR_NAME | in the parser evaluation context.
        """
        return self.parser.eval(py_expr, {varnames.CURRENT_NODE_VAR_NAME: self})

    raw_value: str = field(default_factory=_kw_only)

    def _unsafe_resolve(self) -> Any:
        if isinstance(self.raw_value, str):
            if self.raw_value[0] == '$':
                return self.eval(self.raw_value[1:])
            elif self.raw_value[0] == '\\':
                return self.raw_value[1:]
            else:
                return self.raw_value
        else:
            return self.raw_value
