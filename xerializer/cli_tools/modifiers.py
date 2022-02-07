from .ast_parser import register
from functools import partial
import yaml
from .nodes import FLAGS
from .dict_container import KeyNode
from .nodes import Node
from .tree_builder import AlphaConf
from pathlib import Path
from .functions import cwd
from .utils2 import _Unassigned
from .varnames import DEFAULT_EXTENSION


@register('parent')
def parent(_node: Node = _Unassigned, levels=1):
    """
    Returns, for the given node, the ancestor at the specified number of levels up. Use ``levels=0`` to denote the node itself.
    """

    # Check if this is a modification call or a modifier definition call.
    node = _node
    if node is _Unassigned:
        return partial(parent, levels=levels)

    #
    for _ in range(levels):
        node = node.parent
        if node is None:
            raise Exception(f'Attempted to get the parent of root node {node}!')
    return node


@register('hidden')
def hidden(node):
    node.flags.add(FLAGS.HIDDEN)


@register('load')
def load(_node: KeyNode = _Unassigned, ext=DEFAULT_EXTENSION):
    """
    Resolves ``node.value`` and treats the resolved value as a file path whose data will be used to replace the ``node.value``node. If the path is relative, two possibilities exist:

    1. An ancestor node was loaded from a file (the ancestor file), in which case the relative path is interpreted to be relative to the ancestor file folder.
    2. No ancestor node was loaded from a file, in which case the relative path is interpreted to be relative to the current working directory.

    Paths can be explicitly made to be relative to the current working directory with function :func:`functions.cwd`.

    .. rubric:: Workflow

    The normal ``load`` workflow is as follows:

    1. Modification of a ``load``-modified key node begins as part of a call to :meth:`AlphaConf.modify` during :class:`AlphaConf` initialization.
    2. The target file path is obtained by resolving the key node's value attribute using ``node.value()``.
    3. The data in the target file path is loaded and used to built a sub-tree.
    4. The sub-tree is used to replace the original :attr:`node.value` node in the original `AlphaConf` node tree.
    5. All modifiers all applied to all nodes of the newly inserted sub-tree.
    6. Modification of the original sub-tree as part of the :meth:`AlphaConf.modify` call continues with the remaining nodes.

    .. rubric:: Syntax

    A modifier can be added to the modifiers list using one of these syntaxes

    * load
    * load()
    * load(ext='.yaml')


    :param ext: The default extension to add to files without an extension.
    """

    # Check if this is a modification call or a modifier definition call.
    node = _node
    if node is _Unassigned:
        return partial(load, ext=ext)

    # Get absolute path
    path = Path(node.value())
    if not path.is_absolute():
        root_path = source_file.parent if (source_file := node.source_file) else cwd()
        path = root_path / path

    # Set default extension
    if not path.suffix:
        path = path.with_suffix(ext)

    # Load the data
    with open(path, 'rt') as fo:
        text = fo.read()
    raw_data = yaml.safe_load(text)

    # Build the new node sub-tree
    ac = node.alpha_conf_obj
    new_node = AlphaConf.build_node_tree(raw_data, parser=ac.parser)
    new_node._source_file = path

    # Replace the new node as the value in the original KeyNode.
    node.replace(node.value, new_node)

    # Modify the new node sub-tree
    ac.modify(new_node)

    # Return the new node so that all subsequent modifications are relative to this new node
    return new_node
