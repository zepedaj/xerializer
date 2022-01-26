import re
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from threading import RLock
from typing import Tuple, Dict


def _n(name, expr):
    return f'(?P<{name}>{expr})'


@dataclass
class AutonamePattern:
    """
    Represents a pattern with named groups that have sequential numbers attached to them as suffixes.

    The pattern can also contain other :class:`AutoName` patterns for substitution.

    .. warning:: Calling the meth:`__str__` method of this object (even implicitly through ``print(obj)``) will modify the object by advancing the counter. This enables support for situations where the same nested pattern is used more than once in the same expression, e.g., ``'{pattern}{pattern}'``

    .. test-code::

      # Simple auto-name pattern
      sp = AutonamePattern('(?P<tag>Hello)', ['tag'])

      # Composed auto-name pattern
      cp = AutonamePattern('{x}(?P<tag> World)', ['tag'], {'x':sp})

      # Match only the first pattern
      print(str(sp))
      assert re.match(sp, 'Hello')
      print(str(sp))

      # Match composed pattern
      print(str(cp))
      assert re.match(cp, 'Hello World')
      print(str(sp))
      print(str(cp))

    """

    pattern: str
    names: Tuple[str]
    nested_patterns: Dict[str, 'AutonamePattern'] = field(default_factory=dict)
    _k: int = 0
    _lock: RLock = field(default_factory=RLock)
    _frozen: bool = False

    def next_name(self, _name):
        """
        Generates the auto-numbered name.
        """
        return f'{_name}_{self._k}'

    def view(self):
        """
        Compiles the pattern to a string and without advancing the counters.
        """
        with ExitStack() as stack:
            all_patterns = [self]+list(self.nested_patterns.values())
            [stack.enter_context(x._lock) for x in all_patterns]
            all_ks = [(x, x._k) for x in all_patterns]
            try:
                return str(self)
            finally:
                for (x, _k) in all_ks:
                    x._k = _k

    def __str__(self):
        """
        Compiles the pattern to a string and advances the counter.
        """

        with self._lock:

            # Replace tags
            out = self.pattern
            for _name in self.names:
                out = out.replace(f'<{_name}>', f'<{self.next_name(_name)}>')

            # Replace nested patterns
            out = out.format(**self.nested_patterns)

            #
            if not self._frozen:
                self._k += 1

            return out


class pxs:
    """
    Contains base regex patterns.
    """

    # abc0, _abc0 (not 0abc)
    VARNAME = '[a-zA-Z_]+[a-zA-Z_0-9]*'

    # Matches VARNAME's and
    # abc0.def1 (not abc.0abc, abc., abc.def1. )
    NS_VARNAME = VARNAME + f'(\\.{VARNAME})*(?!\\.)(?![a-zA-Z0-9_])'

    # \\, \\\\, \\\\\\, not \, \\\
    EVEN_SLASHES = r'(?<!\\)(\\\\)*'
    ODD_SLASHES = r'\\(\\\\)*'

    # $abc, \\$abc, \\\\$abc.def
    ATTR = f"{_n('slash', EVEN_SLASHES)}\\$(?P<name>{NS_VARNAME})"

    # abc, a\$, \#b, \'a, a\"bc not 'abc', "abc", a'bc, a"bc, a\\$
    UNQUOTED_LITERAL = (
        '('
        # No spaces, \, $, #, ' or "
        r'[^\s\\\$\#\'\"]+' '|'
        # A sequence of escape sequences
        f'({ODD_SLASHES}[\\$\\#\\\'\\"])*'
        ')+'
    )

    # 'abc', "a$", '#b', '\#', "abc", not 'abc, abc", a\\$ 'a'bc'
    QUOTED_LITERAL = f'(?P<q>[\\\'\\"])[^(?P=q)]*(?P=q)'
    # $fxnname(arg), $fxnname(arg0, arg1), $fxnname(arg0, ... kwarg0=val0, ...)
    #

    LITERAL = f'({UNQUOTED_LITERAL}|{QUOTED_LITERAL})'

    # "abc, def, '123' "
    ARG_LIST = f'({LITERAL}(\\s*,\\s*{LITERAL})*)?'

    FXN_CALL = f'{ATTR}\\(\\)'


def parse(val: str):
    while (matches := list(re.finditer(
            '[^\\]\\$(?P<fxn>[a-z_]+[\\.a-z_0-9]*[a-z_0-9])', 'abc$fxn(def$fxn2(ghi))'))):
        pass
