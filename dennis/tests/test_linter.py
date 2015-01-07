from unittest import TestCase
import os
import sys
import textwrap

from nose.tools import eq_, ok_
from click.testing import CliRunner
import polib

from dennis.cmdline import lint
from dennis.linter import (
    BlankLintRule,
    MalformedNoTypeLintRule,
    MalformedMissingRightBraceLintRule,
    MalformedMissingLeftBraceLintRule,
    MismatchedHTMLLintRule,
    MissingVarsLintRule,
    InvalidVarsLintRule,
    UnchangedLintRule,
    LintedEntry,
    Linter
)
from dennis.templatelinter import (
    HardToReadNamesTLR,
    OneCharNamesTLR,
    MultipleUnnamedVarsTLR,
)
from dennis.tools import VariableTokenizer
from dennis.tests import build_po_string, skip_if, tempdir


class LintCmdTest(TestCase):
    def test_empty(self):
        res = CliRunner().invoke(lint, [])
        eq_(res.exit_code, 1)
        assert 'Nothing to work on' in res.output

    def test_basic(self):
        with tempdir() as dir_:
            pofile = build_po_string(
                '#: foo/foo.py:5\n'
                'msgid "Foo: %(l)s"\n'
                'msgstr "Gmorp!"\n')

            fn = os.path.join(dir_, 'messages.po')
            with open(fn, 'w') as fp:
                fp.write(pofile)

            res = CliRunner().invoke(lint, ['--no-color', fn])

            # The dennis version will change and the temp directory
            # we're using will change, so we're lenient when checking
            # the first two lines.
            line, output = res.output.split('\n', 1)
            assert line.startswith('dennis version')
            line, output = output.split('\n', 1)
            assert line.startswith('>>> Working on')

            # Note: This test will fail if we ever tweak the
            # output. That's ok--just verify the new output and update
            # the test.
            eq_(output,
                textwrap.dedent(u"""\
                W202: missing variables: %(l)s
                15:#: foo/foo.py:5
                16:msgid "Foo: %(l)s"
                17:msgstr "Gmorp!"

                Totals
                  Warnings:     1
                  Errors:       0

                """))

    def test_no_files_to_work_on(self):
        res = CliRunner().invoke(lint, ['foo'])
        eq_(res.exit_code, 1)
        assert 'Nothing to work on.' in res.output

    def test_file_not_exists(self):
        with tempdir() as dir_:
            fn = os.path.join(dir_, 'messages.po')
            res = CliRunner().invoke(lint, [fn])

            eq_(res.exit_code, 1)
            assert (
                'IOError' in res.output
                or 'OSError' in res.output
            )
            assert 'does not exist' in res.output

    def test_basic_pot(self):
        with tempdir() as dir_:
            pofile = build_po_string(
                '#: foo/foo.py:5\n'
                'msgid "Foo: %(l)s"\n'
                'msgstr ""\n')

            fn = os.path.join(dir_, 'messages.pot')
            with open(fn, 'w') as fp:
                fp.write(pofile)

            res = CliRunner().invoke(lint, [fn])

            assert '>>> Working on:' in res.output
            # FIXME: flesh out this test case


class LinterTest(TestCase):
    def test_linter(self):
        pofile = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        linter = Linter(
            ['python-format', 'python-brace-format'],
            ['E201', 'W202']
        )
        msgs = linter.verify_file(pofile)

        # No warnings or errors, so there are no messages.
        eq_(len(msgs), 0)

    def test_linter_fuzzy_strings(self):
        pofile = build_po_string(
            '#, fuzzy\n'
            '#~ msgid "Most Recent Message"\n'
            '#~ msgid_plural "Last %(count)s Messages"\n'
            '#~ msgstr[0] "Les {count} derniers messages"\n'
            '#~ msgstr[1] "Les {count} derniers messages"\n')

        linter = Linter(
            ['python-format', 'python-brace-format'],
            ['E201', 'W202']
        )
        msgs = linter.verify_file(pofile)

        # There were no non-fuzzy strings, so nothing to lint.
        eq_(len(msgs), 0)

    def test_linter_untranslated_strings(self):
        pofile = build_po_string(
            '#, fuzzy\n'
            '#~ msgid "Most Recent Message"\n'
            '#~ msgid_plural "Last %(count)s Messages"\n'
            '#~ msgstr[0] ""\n'
            '#~ msgstr[1] ""\n')

        linter = Linter(
            ['python-format', 'python-brace-format'],
            ['E201', 'W202']
        )
        msgs = linter.verify_file(pofile)

        # There were no translated strings, so nothing to lint.
        eq_(len(msgs), 0)


def build_linted_entry(po_data):
    po = polib.pofile(build_po_string(po_data))
    poentry = list(po)[0]
    return LintedEntry(poentry)


class LintRuleTestCase(TestCase):
    vartok = VariableTokenizer(['python-format', 'python-brace-format'])


class MalformedNoTypeLintRuleTest(LintRuleTestCase):
    lintrule = MalformedNoTypeLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_python_var_with_space(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(count)s view"\n'
            'msgid_plural "%(count)s views"\n'
            'msgstr[0] "%(count) zoo"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E101')
        eq_(msgs[0].msg, 'type missing: %(count)')

    def test_python_var_end_of_line(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(count)s"\n'
            'msgid_plural "%(count)s"\n'
            'msgstr[0] "%(count)"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E101')
        eq_(msgs[0].msg, 'type missing: %(count)')

    def test_python_var_not_malformed(self):
        """This used to be a false positive"""
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(stars)s by %(user)s on %(date)s (%(locale)s)"\n'
            'msgstr "%(stars)s de %(user)s el %(date)s (%(locale)s)"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    # FIXME - test to make sure it doesn't do anything for
    # non-python-format situations.


class MalformedMissingRightBraceLintRuleTest(LintRuleTestCase):
    lintrule = MalformedMissingRightBraceLintRule()

    def test_python_var_missing_right_curly_brace(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{foo} bar is the best thing ever"\n'
            'msgstr "{foo) bar is the best thing ever"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E102')
        eq_(msgs[0].msg,
            'missing right curly-brace: {foo) bar is the best thing ever')

        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{foo}"\n'
            'msgstr "{foo"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E102')
        eq_(msgs[0].msg,
            'missing right curly-brace: {foo')

    def test_python_var_missing_right_curly_brace_two_vars(self):
        # Test right-most one
        linted_entry = build_linted_entry(
            'msgid "Value for key \\"{0}\\" exceeds the length of {1}"\n'
            'msgstr "Valor para la clave \\"{0}\\" excede el tamano de {1]"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E102')
        eq_(msgs[0].msg,
            'missing right curly-brace: {1]')

        # Test left-most one
        linted_entry = build_linted_entry(
            'msgid "Value for key \\"{0}\\" exceeds the length of {1}"\n'
            'msgstr "Valor para la clave \\"{0]\\" excede el tamano de {1}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E102')
        eq_(msgs[0].msg,
            'missing right curly-brace: {0]" excede el tamano de {')


class MalformedMissingLeftBraceLintRuleTest(LintRuleTestCase):
    lintrule = MalformedMissingLeftBraceLintRule()

    def test_python_var_missing_left_curly_brace(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{product} Support Forum"\n'
            'msgstr "product}-Hilfeforum"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E103')
        eq_(msgs[0].msg,
            'missing left curly-brace: product}')

        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{q} | {product} Support Forum"\n'
            'msgstr "{q} | product}-Hilfeforum"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E103')
        eq_(msgs[0].msg,
            'missing left curly-brace: } | product}')

        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/question_details.html:14\n'
            'msgid "{q} | {product} Support Forum"\n'
            'msgstr "{q} | {product}} foo bar"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E103')
        eq_(msgs[0].msg,
            'missing left curly-brace: }}')


class MissingVarsLintRuleTest(LintRuleTestCase):
    lintrule = MissingVarsLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_missing(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W202')
        eq_(msgs[0].msg,
            'missing variables: {foo}')

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo} {bar} {baz}"\n'
            'msgstr "Oof: {foo}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W202')
        eq_(msgs[0].msg,
            'missing variables: {bar}, {baz}')

    def test_complex(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {bar} {baz}"\n'
            'msgstr "Oof: {foo} {bar}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W202')
        eq_(msgs[0].msg,
            'missing variables: {baz}')

    def test_plurals(self):
        # It's possible for the msgid to have no variables in it and
        # the msgid_plural to have variables in it. msgstr[n] strings
        # should be compared against the set of variables in msgid and
        # msgid_plural. This tests the common case.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "1 reply"\n'
            'msgid_plural "{n} replies"\n'
            'msgstr[0] "{n} mooo"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_plurals_not_missing(self):
        # If the msgstr doesn't have variables that are in msgid or
        # msgid_plural, that's ok since we don't know which plurality
        # it is.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "1 post"\n'
            'msgid_plural "{0} posts"\n'
            'msgstr[0] "1 moo"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_double_percent(self):
        # Double-percent shouldn't be picked up as a variable.
        # Issue #28.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "50% of the traffic"\n'
            'msgstr "more than 50%% of the traffic"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_urlencoded_urls(self):
        # urlencoding uses % and that shouldn't get picked up
        # as variables.
        # Issue #27.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "OMG! Best url is http://example.com/foo"\n'
            'msgstr "http://example.com/foo%20%E5%B4%A9%E6%BA%83 is best"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)


class InvalidVarsLintRuleTest(LintRuleTestCase):
    lintrule = InvalidVarsLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_invalid(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof: {foo}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E201')
        eq_(msgs[0].msg,
            'invalid variables: {foo}')

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo} {bar} {baz}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E201')
        eq_(msgs[0].msg,
            'invalid variables: {bar}, {baz}')

    def test_complex(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {bar} {baz}"\n'
            'msgstr "Oof: {foo} {bar}"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'err')
        eq_(msgs[0].code, 'E201')
        eq_(msgs[0].msg,
            'invalid variables: {foo}')

    def test_plurals(self):
        # It's possible for the msgid to have no variables in it and
        # the msgid_plural to have variables in it. msgstr[n] strings
        # should be compared against the set of variables in msgid and
        # msgid_plural. This tests the common case.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "1 reply"\n'
            'msgid_plural "{n} replies"\n'
            'msgstr[0] "{n} mooo"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_double_percent(self):
        # Double-percent shouldn't be picked up as a variable.
        # Issue #28.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "50% of the traffic"\n'
            'msgstr "more than 50%% of the traffic"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_urlencoded_urls(self):
        # urlencoding uses % and that shouldn't get picked up
        # as variables.
        # Issue #27.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "OMG! Best url is http://example.com/foo"\n'
            'msgstr "http://example.com/foo%20%E5%B4%A9%E6%BA%83 is best"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)


class BlankLintRuleTestCase(LintRuleTestCase):
    lintrule = BlankLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr ""\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_whitespace(self):
        testdata = [
            ' ',
            '  ',
            '\t'
        ]
        for data in testdata:
            linted_entry = build_linted_entry(
                '#: foo/foo.py:5\n'
                'msgid "Foo"\n'
                'msgstr "%s"\n' % data)

            msgs = self.lintrule.lint(self.vartok, linted_entry)
            eq_(len(msgs), 1)
            eq_(msgs[0].kind, 'warn')
            eq_(msgs[0].code, 'W301')
            eq_(msgs[0].msg, u'translated string is solely whitespace')


class UnchangedLintRuleTestCase(LintRuleTestCase):
    lintrule = UnchangedLintRule()

    def test_unchanged(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Foo"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W302')
        eq_(msgs[0].msg,
            u'translated string is same as source string')


class MismatchedHTMLLintRule(LintRuleTestCase):
    lintrule = MismatchedHTMLLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "<b>Foo</b>"\n'
            'msgstr "<b>ARGH</b>"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 0)

    def test_fail(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "<b>Foo</b>"\n'
            'msgstr "<em>ARGH</em>"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W303')
        eq_(msgs[0].msg,
            'different html: "</b>" vs. "</em>"')

    def test_different_numbers(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "<b>Foo"\n'
            'msgstr "<b>ARGH</b>"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W303')
        eq_(msgs[0].msg,
            'different html: "<b>" vs. "</b>"')

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "<b>Foo</b>"\n'
            'msgstr "<b>ARGH"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W303')
        eq_(msgs[0].msg,
            'different html: "</b>" vs. "<b>"')

    @skip_if(lambda: not sys.version.startswith('2.6'))
    def test_invalid_html_26(self):
        linted_entry = build_linted_entry(
            u'#: foo/foo.py:5\n' +
            u'msgid "<a>Foo</a>"\n' +
            u'msgstr "<a>ARGH</\u0430>"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W304')
        # HTMLParser in Python 2.6 throws an HTMLParseError, so we
        # get a different error code.
        ok_(msgs[0].msg.startswith(u'invalid html: msgstr has invalid'))

    @skip_if(lambda: sys.version.startswith('2.6'))
    def test_invalid_html_gt_26(self):
        linted_entry = build_linted_entry(
            u'#: foo/foo.py:5\n' +
            u'msgid "<a>Foo</a>"\n' +
            u'msgstr "<a>ARGH</\u0430>"\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        eq_(msgs[0].kind, 'warn')
        eq_(msgs[0].code, 'W303')
        # HTMLParser doesn't recognize </\u0430> as a valid HTML tag,
        # so you end up with:
        #
        # [<html </a>>, <html <a>>]
        #
        # vs.
        #
        # [<html <a>>]
        eq_(msgs[0].msg, u'different html: "</a>" vs. "<a>"')


class TLRTestCase(TestCase):
    vartok = VariableTokenizer(['python-format', 'python-brace-format'])


class HardToReadNamesTLRTestCase(TLRTestCase):
    lintrule = HardToReadNamesTLR()

    def test_hard_to_read_names(self):
        for c in ('o', 'O', '0', 'l', '1'):
            linted_entry = build_linted_entry(
                '#: foo/foo.py:5\n'
                'msgid "Foo: %(' + c + ')s"\n'
                'msgstr ""\n')

            msgs = self.lintrule.lint(self.vartok, linted_entry)
            eq_(len(msgs), 1)

            linted_entry = build_linted_entry(
                '#: foo/foo.py:5\n'
                'msgid "Foo: {' + c + '}"\n'
                'msgstr ""\n')

            msgs = self.lintrule.lint(self.vartok, linted_entry)
            eq_(len(msgs), 1)
        # FIXME: flesh out this test


class MultipleUnnamedVarsTLRTestCase(TLRTestCase):
    lintrule = MultipleUnnamedVarsTLR()

    def test_multi_vars_no_name(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: %s %s"\n'
            'msgstr ""\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {} {}"\n'
            'msgstr ""\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        # FIXME: flesh out this test


class OneCharNamesTLRTestCase(TLRTestCase):
    lintrule = OneCharNamesTLR()

    def test_one_character_names(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: %(c)s"\n'
            'msgstr ""\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {c}"\n'
            'msgstr ""\n')

        msgs = self.lintrule.lint(self.vartok, linted_entry)
        eq_(len(msgs), 1)
        # FIXME: flesh out this test
