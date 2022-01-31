from dataclasses import dataclass, field
import abc
from threading import RLock
from .nodes import Node, _kw_only
from typing import List


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


@dataclass
class ListContainer(Container):
    children: List[Node] = field(default_factory=_kw_only)
