import ast
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

# WARNING: Using python precision can result in hangs from malicious input.
PYTHON_PRECISION = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                    ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
                    ast.USub: op.neg}

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


def register(name, value, /, overwrite=False, context=DEFAULT_CONTEXT):
    """
    Registers a variable in the specified context (the default context by default).
    """
    if not overwrite and name in DEFAULT_CONTEXT:
        raise Exception(f'A variable with name `{name}` already exists in the context.')
    context[name] = value


class Parser:

    def __init__(self, context=None, operators='numpy'):
        """
        :param operators: ['numpy'|'python'] Use math operators from Numpy or Python. Python math operators have infinite precision and unbounded compute time, resulting possibly in system hangs. Numpy operators have finite precision but bounded compute time.

        .. warning:: Using python precision can result in system hangs from malicious input given Python's infinite precision (e.g., ``parser.eval('9**9**9**9**9**9**9')`` will hang).
        """
        self._operators = dict({'numpy': NUMPY_PRECISION, 'python': PYTHON_PRECISION})[operators]

        self._context = {**DEFAULT_CONTEXT, **(context or {})}

    def register(self, name, value, overwrite=False):
        register(name, value, overwrite=overwrite, context=self._context)

    def get_from_context(self, name):
        try:
            return self._context[name]
        except KeyError:
            raise UndefinedFunction(f'Name `{name}` undefined in parser context.')

    def eval(self, expr):
        """

        Extension of `https://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string`.

        >>> parser.eval('2^6')
        4
        >>> parser._evalexpr('2**6')
        64
        >>> parser._evalexpr('1 + 2*3**(4^5) / (6 + -7)')
        -5.0
        """
        if len(expr) > MAX_EXPR_LEN:
            raise Exception('The input expression has length {len(expr)} > {MAX_EXPR_LEN}.')
        return self._eval(ast.parse(expr, mode='eval').body)

    def _eval(self, node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return self._operators[type(node.op)](self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return self._operators[type(node.op)](self._eval(node.operand))
        elif isinstance(node, ast.Call):
            return self.get_from_context(node.func.id)(
                *[self._eval(x) for x in node.args],
                **{x.arg: self._eval(x.value) for x in node.keywords})
        elif isinstance(node, ast.Name):
            return self.get_from_context(node.id)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval(x) for x in node.elts)
        else:
            raise UnsupportedGrammarComponent(node)
