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
        sp = mdl.AutonamePattern('(?P<htag>Hello)', ['htag'])

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', ['wtag'], {'x': sp})

        # Match only the first pattern
        assert sp.view() == (sp0_expected := '(?P<htag_0>Hello)')
        assert re.match(sp0_actual := str(sp), 'Hello')
        assert sp0_actual == sp0_expected

        # Match composed pattern
        assert(
            cp.view() ==
            (cp0_expected :=
             '(?P<htag_1>Hello) (?P<htag_2>Hello) (?P<htag_3>Hello) (?P<wtag_0>World)'))
        assert re.match(
            cp0_actual := str(cp), 'Hello Hello Hello World')
        assert cp0_actual == cp0_expected
        assert sp.view() == '(?P<htag_4>Hello)'
        assert (
            cp.view() ==
            '(?P<htag_4>Hello) (?P<htag_5>Hello) (?P<htag_6>Hello) (?P<wtag_1>World)')
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
                new_name = self.next_name(_name)
                out = out.replace(f'<{_name}>', f'<{new_name}>')
                out = out.replace(f'(?P={_name})', f'(?P={new_name})')

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

    # abc, a\$, \#b, \'a, a\"bc, a\, not 'abc', "abc", a'bc, a"bc, a\\, a,$
    UNQUOTED_LITERAL = (
        '('
        # No spaces, \, $, #, ' or "
        r'[^\s\\\$\#\'\"\,]+' '|'
        # A sequence of escape sequences
        f'({ODD_SLASHES}[\\$\\#\\\'\\"\\,])+'
        ')+'
    )

    # 'abc', "a$", '#b', '\#', "abc", not 'abc, abc", a\\$ 'a'bc'
    QUOTED_LITERAL = AutonamePattern(f'(?P<q>[\\\'\\"])[^(?P=q)]*(?P=q)', ['q'])
    # $fxnname(arg), $fxnname(arg0, arg1), $fxnname(arg0, ... kwarg0=val0, ...)
    #

    LITERAL = AutonamePattern(
        '({UNQUOTED_LITERAL}|{QUOTED_LITERAL})',
        {'UNQUOTED_LITERAL': UNQUOTED_LITERAL, 'QUOTED_LITERAL': QUOTED_LITERAL})

    # "abc, def, '123' "
    ARG_LIST = AutonamePattern('({LITERAL}(\\s*,\\s*{LITERAL})*)?', {'LITERAL': LITERAL})

    FXN_CALL = f'{ATTR}\\(\\)'


def parse(val: str):
    while (matches := list(re.finditer(
            '[^\\]\\$(?P<fxn>[a-z_]+[\\.a-z_0-9]*[a-z_0-9])', 'abc$fxn(def$fxn2(ghi))'))):
        pass
