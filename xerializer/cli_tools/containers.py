from dataclasses import dataclass, field
from .exceptions import NotAChildOfError
import abc
from threading import RLock
from .nodes import Node
from typing import List, Union


@dataclass
class Container(Node):

    lock: RLock = field(default_factory=RLock)

    @property
    @abc.abstractmethod
    def children(self): return {}

    @abc.abstractmethod
    def add(self, node: Node):
        """
        Add the specified node to the container.
        """

    @abc.abstractmethod
    def remove(self, node: Node):
        """
        Remove the specified node from the container.
        """

    def __getitem__(self, *args) -> Node:
        """
        Returns the specified node or nodes.
        """
        return self.children.__getitem__(*args)

    @abc.abstractmethod
    def get_child_qual_name(self, child_node):
        """
        Returns the name of the specified child in the container as a string.
        """


@dataclass
class ListContainer(Container):

    children: List[Node] = None

    def __init__(self, **kwargs):
        self.children = []
        super().__init__(**kwargs)

    def add(self, node: Node):
        with self.lock:
            self.children.append(node)

    def remove(self, index: Union[int, Node]):
        """
        Removes the node (if index is a Node) or the node at the specified position (if index is an int).
        """
        with self.lock:
            if isinstance(index, int):
                self.children.pop(index)
            elif isinstance(index, Node):
                self.children.remove(index)
            else:
                raise TypeError(f'Invalid type {type(index)} for arg `index`.')

    def _unsafe_resolve(self):
        with self.lock:
            return [n.resolve() for n in self.children]

    def get_child_qual_name(self, child_node):

        #
        for k, contained_child in enumerate(self.children):
            if child_node is contained_child:
                return self._derive_qual_name(str(k))
        #
        raise NotAChildOfError(child_node, self)
