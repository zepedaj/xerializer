from dataclasses import dataclass, field
from threading import RLock
from nodes import Node, _kw_only, KeyNode
from typing import List, Dict, Union


@dataclass
class Container(Node):

    lock: RLock = field(default_factory=RLock)

    # @abc.abstractmethod
    @property
    def children(self): ...

    # @abc.abstractmethod
    def add(self, node: Node):
        """
        Add the specified node to the container.
        """

    # @abc.abstractmethod
    def remove(self, node: Node):
        """
        Remove the specified node from the container.
        """


@dataclass
class ListContainer(Container):
    children: List[Node] = field(default_factory=_kw_only)


@dataclass
class DictContainer(Container):

    children: Dict[Node, Node] = field(default_factory=_kw_only)
    # Both key and value will be the same KeyNode. This will
    # enable situations where the node's name is changed.
    # It also supports replacing nodes with the same name and,
    # given the KeyNodes.__eq__ implementation, this approach will also support
    # string indexing.
    #
    # Using a set seemed like a more natural solution, but I was unable to
    # retrieve an object from a set given a string key (I tried `node_set.intersection(key)`,
    # and `{key}.intersection(node_set)` )
    #
    # WARNING: Changing the name of a key node without taking care that
    # that node is not a part of a dictionary where another KeyNode exists with the
    # same name will result in unexpected behavior.

    def add(self, node: KeyNode):
        """
        Adds the node to the container or replaces the node with the same name if one exists.
        """
        self.children[node] = node

    def remove(self, node: Union[KeyNode, str]):
        self.children.pop(node)

    def resolve(self):
        """
        Returns the resolved dictionary.
        """
        return {key.name: self[key] for key in
                (node.name for node in self.children)}

    def __getitem__(self, key: str):
        """
        Returns the resolved value for the specified key.
        """
        if not (found_nodes := self.children.intersection(key)):
            raise KeyError(key)
        else:
            assert len(found_nodes)
            return next(iter(found_nodes)).resolve()
