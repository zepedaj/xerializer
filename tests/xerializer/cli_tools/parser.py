from xerializer.cli_tools import parser as mdl
from unittest import TestCase
import re


class TestAutonamePattern(TestCase):

    def test_all(self):
        # Simple auto-name pattern
        sp = mdl.AutonamePattern('(?P<htag>Hello)', ['htag'])

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', ['wtag'], {'x': sp})

        # Match only the first pattern
        self.assertEqual(sp.view(), sp0_expected := '(?P<htag_0>Hello)')
        assert re.match(sp0_actual := str(sp), 'Hello')
        self.assertEqual(sp0_actual, sp0_expected)

        # Match composed pattern
        self.assertEqual(
            cp.view(), cp0_expected :=
            '(?P<htag_1>Hello) (?P<htag_2>Hello) (?P<htag_3>Hello) (?P<wtag_0>World)')
        assert re.match(
            cp0_actual := str(cp), 'Hello Hello Hello World')
        self.assertEqual(cp0_actual, cp0_expected)
        self.assertEqual(sp.view(), '(?P<htag_4>Hello)')
        self.assertEqual(
            cp.view(),
            '(?P<htag_4>Hello) (?P<htag_5>Hello) (?P<htag_6>Hello) (?P<wtag_1>World)')


class TestPxs(TestCase):
    def test_all(self):
        for name, matches, non_matches in [
                ('VARNAME', vnm := ('abc0', '_abc0'), vnnm := ('0abc',)),
                ('NS_VARNAME', vnm+('abc0.def1',), vnnm+('abc.0abc', 'abc.', 'abc.def1.')),
                # Any string will match zero-slashes not preceded by slash
                # at the start of the string, including odd slashes. Skipping
                # Non-matching tests for even slashes.
                ('EVEN_SLASHES', (r'\\', r'\\\\', r'\\\\\\'), tuple()),
                ('ATTR',
                 ('$abc', r'\\$abc', r'\\\\$abc.def', '$abc'),
                 (r'\$abc', r'\\\$abc.def0', '$0abc')),
                ('UNQUOTED_LITERAL',
                 ('abc', r'a\$', r'\$b', r'a\#', r'\#b', r'\'a', r'a\"bc'),
                 ("'abc'", '"abc"', "a'bc", 'a"bc', r'a\\$', r'a b')),
                ('QUOTED_LITERAL',
                 ("'abc'", '"a$"', "'#b'", "'\\#'", '"abc"', '"ab\"c"'),
                 ("'abc", 'abc"', 'a\\$' "'a'bc'"))
        ]:
            [self.assertTrue(re.match('^'+getattr(mdl.pxs, name)+'$', match))
             for match in matches]
            [self.assertFalse(re.match('^'+getattr(mdl.pxs, name)+'$', non_match))
             for non_match in non_matches]
