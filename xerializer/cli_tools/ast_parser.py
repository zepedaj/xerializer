import ast
from dataclasses import dataclass
from typing import Dict, Any
import builtins
import operator as op
import numpy as np

# supported operators
MAX_EXPR_LEN = int(1e4)

# Exceptions


class UndefinedFunction(KeyError):
    pass


class UnsupportedGrammarComponent(TypeError):
    pass


NUMPY_PRECISION = {key: (lambda *args, val=val: val(*args).item())
                   for key, val in
                   {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply,
                    ast.Div: np.divide, ast.Pow: np.power, ast.BitXor: np.bitwise_xor,
                    ast.USub: np.negative}.items()}

PYTHON_PRECISION = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                    ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
                    ast.USub: op.neg}
"""
.. warning:: Using python (infinite) precision can result in hangs from malicious input.
"""

BUILTIN_SCALAR_TYPES = (
    'float', 'int', 'bool', 'bytes', 'str')
BUILTIN_ITERABLE_TYPES = (
    'list', 'tuple', 'dict', 'set')  # Require __iter__
"""
All these types from the ``builtins`` module are supported both as part of expressions and as node modifiers.
"""

DEFAULT_CONTEXT = {
    **{key: getattr(builtins, key) for key in BUILTIN_SCALAR_TYPES + BUILTIN_ITERABLE_TYPES}
}
"""
Contains the default context accessible to parsers.
"""


class _Unassigned:
    pass


@dataclass
class register:
    """
    Register a variable in the default context.

    Example:

    .. test-code::

      my_var = 'my variable'

      # As a stand-alone call
      register('my_var', my_var)

      # As a function decorator
      @register('my_function')
      def my_function: pass

    """

    def __init__(self, name: str, value: Any = _Unassigned, *, overwrite: bool = False,
                 context: Dict[str, Any] = DEFAULT_CONTEXT):
        """
        :param name: The name of the variable in the context.
        :param overwrite:  Whether to overwrite the variable if it is already in the context.
        :param context: The context to modify.
        """

        self.name = name
        self.overwrite = overwrite
        self.context = context
        self.executed = False

        if value is not _Unassigned:
            self._register(value)

    def __call__(self, fxn):
        """
        Registers the input function.
        """
        self._register(fxn)
        return fxn

    def _register(self, value):
        if not self.overwrite and self.name in DEFAULT_CONTEXT:
            raise Exception(f'A variable with name `{self.name}` already exists in the context.')
        self.context[self.name] = value


class Parser:

    def __init__(self, extra_context=None, operators='numpy'):
        """
        :param extra_context: Extra variables to append to the default context. These will overwrite existing variables of the same name.
        :param operators: ['numpy'|'python'] Use math operators from Numpy or Python. Python math operators have infinite precision and unbounded compute time, resulting possibly in system hangs. Numpy operators have finite precision but bounded compute time.

        .. warning:: Using python precision can result in system hangs from malicious input given Python's infinite precision (e.g., ``parser.eval('9**9**9**9**9**9**9')`` will hang).
        """
        self._operators = dict({'numpy': NUMPY_PRECISION, 'python': PYTHON_PRECISION})[operators]
        self._context = {**DEFAULT_CONTEXT, **(extra_context or {})}

    def register(self, name, value, overwrite=False):
        register(name, value, overwrite=overwrite, context=self._context)

    def get_from_context(self, name, context=None):
        try:
            return (context or self._context)[name]
        except KeyError:
            raise UndefinedFunction(f'Name `{name}` undefined in parser context.')

    def eval(self, expr, extra_context=None):
        """
        Evaluates the python expression ``expr``.

        The parser's context is extended by ``extra_context`` if provided.
        """

        extended_context = {**self._context, **extra_context} if extra_context else None
        if len(expr) > MAX_EXPR_LEN:
            raise Exception('The input expression has length {len(expr)} > {MAX_EXPR_LEN}.')
        return self._eval(ast.parse(expr, mode='eval').body, extended_context)

    def _eval(self, node, context=None):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return self._operators[type(node.op)](
                self._eval(node.left, context),
                self._eval(node.right, context))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return self._operators[type(node.op)](self._eval(node.operand, context))
        elif isinstance(node, ast.Call):
            return self.get_from_context(node.func.id, context)(
                *[self._eval(x, context) for x in node.args],
                **{x.arg: self._eval(x.value, context) for x in node.keywords})
        elif isinstance(node, ast.Name):
            return self.get_from_context(node.id, context)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval(x, context) for x in node.elts)
        else:
            raise UnsupportedGrammarComponent(node)
