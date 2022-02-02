from dataclasses import dataclass
from inspect import stack
from typing import Optional


@dataclass
class ResolvingNode:
    """
    Denotes a node that is being resolved further down in the call stack. A given node being resolved will be added to the first ResolvingNode found going down the call stack.
    """
    node: Optional  # : Optional['Node']

    @classmethod
    def find(self):
        """
        Searches down the stack for the first variable of name `__resolving_node__` and type :class:`ResolvingNode`.
        """
        call_stack = stack()
        for call in call_stack:
            if resolving_node := call.frame.f_locals.get('__resolving_node__', None):
                if not isinstance(resolving_node, ResolvingNode):
                    raise Exception(
                        f'Unexpected type {type(resolving_node)} for variable `__resolving_node__` in function {call.function}.')
                else:
                    return resolving_node

        return ResolvingNode(None)

    def add_dependency(self, dependency_node):
        if self.node is not None:
            if not any(dependency_node is x for x in self.node.dependencies):
                self.node.dependencies.append(dependency_node)
            else:
                raise Exception('Found a dependency cycle!')
