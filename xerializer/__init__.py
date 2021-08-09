r"""
Flexible serialization.

The supported types and their json string formats follow:

.. ipython::

    In [1]: from xerializer import Serializer, Literal

    In [2]: for obj in [
       ...:     0, 0.0, None, True, 'abc',
       ...:     [1,2,'abc', {'a':1}],
       ...:     (1,2,'abc', {'a':1}),
       ...:     {1,2,'abc'},
       ...:     Literal([1,2,(3,4), {'a':0, 'b':1.6}])
       ...:         ]:
       ...:     print(f'# {obj}:',  '\n', f"'{Serializer().dumps(obj)}'", '\n');
       ...:


"""

from .serializer import Serializer
from .abstract_type_serializer import TypeSerializer, Serializable
from .builtin_plugins import Literal

#
__all__ = ['Serializer', 'Literal', 'TypeSerializer', 'Serializable']
