from xerializer.cli_tools import parser as mdl
from unittest import TestCase
import re


class TestAutonamePattern(TestCase):

    def test_doc(self):
        # Simple auto-name pattern
        sp = mdl.AutonamePattern('(?P<htag>Hello)', names=['htag'])

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', {'x': sp}, names=['wtag'])

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

    def test_doc__no_names(self):
        # Simple auto-name pattern
        sp = mdl.AutonamePattern('(?P<htag>Hello)')

        # Composed auto-name pattern
        cp = mdl.AutonamePattern('{x} {x} {x} (?P<wtag>World)', {'x': sp})

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
                 ('abc', r'a\$', r'\$b', r'a\#', r'\#b', r'\'a', r'a\"bc', r'a\,', r"a\""),
                 ("'abc'", '"abc"', "a'bc", 'a"bc', r'a\\$', r'a b', r'a,', ',', ',,', '')),
                ('QUOTED_LITERAL',
                 ("'abc'", '"a$"', "'#b'", "'\\#'", '"abc"', '"ab\"c"', r'"a\""'),
                 ("'abc", 'abc"', 'a\\$' "'a'bc'", "")),
                ('ARG_LIST',
                 ('abc,def,xyz', '1,234,abc', "1,'abc', xyz"),
                 (',', ' , ' 'a,,b', 'a=1', 'a=1,b', '')),
                ('KWARG_LIST',
                 ('abc=1, def=2,ghi=abc', 'abc=1',),
                 ('abc, def', 'abc 1, def=2,ghi=abc', ''))
        ]:
            [self.assertTrue(re.match('^'+str(getattr(mdl.pxs, name))+'$', match))
             for match in matches]
            [self.assertFalse(re.match('^'+str(getattr(mdl.pxs, name))+'$', non_match))
             for non_match in non_matches]

    def test_fxn_call(self):

        pattern = re.compile(f'^{mdl.pxs.FXN_CALL}$')
        for value, arg_list, kwarg_list in [
                ('$add()', None, None),
                ('$add(a,b,c)', 'a,b,c', None),
                ('$add(a=1)', None, 'a=1'),
                ('$add(a=1,b=2)', None, 'a=1,b=2'),
                ('$add(a,b,c,d=1,b=2)', 'a,b,c', 'd=1,b=2'),
        ]:
            self.assertIsNotNone(match := re.match(pattern, value))
            breakpoint()
            self.assertEqual(match['arg_list_0'], arg_list)
            self.assertEqual(match['kwarg_list_0'], kwarg_list)
        for value in [
                '$add(,)',
                '$add(,a)',
                '$add(a=1,b)',
        ]:
            match = re.match(pattern, value)
            self.assertIsNone(match)
