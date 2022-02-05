from .ast_parser import register
from .nodes import FLAGS


@register('parent')
def parent(node, levels=1):
    """
    Returns the ancestor of the node of the specified levels up. Use ``levels=0`` to denote the node itself.
    """
    for _ in range(levels):
        node = node.parent
        if node is None:
            raise Exception(f'Node {node} is a root node!')
    return node


@register('hidden')
def hidden(node):
    node.flags.add(FLAGS.HIDDEN)
