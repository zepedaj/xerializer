import re
from contextlib import ExitStack
from dataclasses import dataclass, field
from threading import RLock
from typing import Optional, Tuple, Dict


def _n(name, expr):
    return f'(?P<{name}>{expr})'


@dataclass
class AutonamePattern:
    """
    Represents a pattern with named groups that have sequential numbers attached to them as suffixes.

    The pattern can also contain other :class:`AutoName` patterns for substitution. The format for other autoname patterns is the same as that for python ``str.format`` syntax (see 'composed auto-name' example below).

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
    nested_patterns: Dict[str, 'AutonamePattern'] = field(default_factory=dict)
    names: Optional[Tuple[str]] = None
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

            # Replace names in pattern
            NAMES = (
                '|'.join(re.escape(x) for x in self.names)
                if self.names
                else r'[a-zA-Z]\w*')

            # Substitute groups
            out = self.pattern
            for GROUP_PREFIX, GROUP_SUFFIX in [
                    ('(?P<', '>'),  # Replaces (?P<name> by (?P<name_k>
                    ('(?P=', ')'),  # Replaces (?P=name) by (?P=name_k)
                    ('(?(', ')'),  # Replaces (?P=name) by (?P=name_k)
            ]:
                out = re.sub(
                    f"(?P<prefix>({pxs.EVEN_SLASHES}|^|[^{pxs.SLASH}]))"
                    f"{re.escape(GROUP_PREFIX)}(?P<name>{NAMES}){re.escape(GROUP_SUFFIX)}",
                    lambda x: f"{x['prefix']}{GROUP_PREFIX}{self.next_name(x['name'])}{GROUP_SUFFIX}",
                    out)

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
    VARNAME = r'[a-zA-Z_]+\w*'

    # Matches VARNAME's and fully qualified versions
    # abc0.def1 (not abc.0abc, abc., abc.def1. )
    NS_VARNAME = AutonamePattern(
        r'{VARNAME}(\.{VARNAME})*(?!\.)(?!\w)', vars())

    # \\, \\\\, \\\\\\, not \, \\\
    SLASH = r'\\'
    EVEN_SLASHES = r'(?<!\\)(\\\\)*'
    ODD_SLASHES = r'\\(\\\\)*'

    # $abc, \\$abc, \\\\$abc.def
    ATTR = AutonamePattern(
        r"(?P<slash>{EVEN_SLASHES})\$(?P<name>{NS_VARNAME})", vars())

    # abc, a\$, \#b, \'a, a\"bc, a\, not 'abc', "abc", a'bc, a"bc, a\\, a,$
    UNQUOTED_LITERAL = (
        '('
        # No un-escaped spaces, $, #, =, ', ", (, ), \
        '[^' + (_qchars := r'\s\$\#\=\'\"\,\(\)\\' + ']|') +
        # A sequence of escape sequences
        f'({ODD_SLASHES}[{_qchars}])+'
        ')+'
    )

    # 'abc', "a$", '#b', '\#', "abc", not 'abc, abc", a\\$ 'a'bc'
    QUOTED_LITERAL = AutonamePattern(
        r'(?P<q>[\'\"])('
        # Non-quote and non slash char
        r'[^(?P=q)\\]' '|'
        # Odd-slashes-escaped non-slash char (including quote)
        '{ODD_SLASHES}[^{SLASH}]' '|'
        # Even number of slashes
        '{EVEN_SLASHES}(?!(?P=q))'
        ')*(?P=q)', vars())
    # $fxnname(arg), $fxnname(arg0, arg1), $fxnname(arg0, ... kwarg0=val0, ...)
    #

    # A string literal
    # "abc, def, '123' "
    LITERAL = AutonamePattern(
        '({UNQUOTED_LITERAL}|{QUOTED_LITERAL})', vars())

    # Arguments in argument lists are interpreted as YAML strings.
    LITERAL_ARG = AutonamePattern(
        '(?P<argval>{LITERAL})', vars())
    ARG_LIST = AutonamePattern(
        r'({LITERAL_ARG}(\s*,\s*{LITERAL_ARG})*)', vars())

    LITERAL_KWARG = AutonamePattern(
        r'(?P<kwname>{VARNAME})\s*=\s*(?P<kwval>{LITERAL})', vars())
    KWARG_LIST = AutonamePattern(
        ARG_LIST.pattern.format(LITERAL_ARG='{LITERAL_KWARG}'), vars())

    FXN_CALL = AutonamePattern(
        r'\$(?P<fxn>{NS_VARNAME})\('
        r'\s*(?P<arg_list>{ARG_LIST})?\s*((?(arg_list),\s*)(?P<kwarg_list>{KWARG_LIST}))?\s*'
        r'\)', vars())


def parse(val: str):
    while (matches := list(re.finditer(
            '[^\\]\\$(?P<fxn>[a-z_]+[\\.a-z_0-9]*[a-z_0-9])', 'abc$fxn(def$fxn2(ghi))'))):
        pass
