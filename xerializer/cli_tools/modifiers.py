from .ast_parser import register


@register('parent')
def parent(node):
    """
    Returns the parent of the node.
    """
    return node.parent
