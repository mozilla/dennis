from unittest import TestCase
import os
import textwrap

from nose.tools import eq_
import polib

from dennis.cmdline import lint_cmd
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
from dennis.minisix import StringIO
from dennis.tools import VariableTokenizer
from dennis.tests import build_po_string, redirect, tempdir


class LintCmdTest(TestCase):
    def test_empty(self):
        stdout = StringIO()
        with redirect(stdout=stdout):
            lint_cmd('test', 'lint', [])

    def test_basic(self):
        with tempdir() as dir_:
            pofile = build_po_string(
                '#: foo/foo.py:5\n'
                'msgid "Foo: %(l)s"\n'
                'msgstr "Gmorp!"\n')

            fn = os.path.join(dir_, 'messages.po')
            with open(fn, 'w') as fp:
                fp.write(pofile)

            stdout = StringIO()
            stderr = StringIO()
            with redirect(stdout=stdout, stderr=stderr):
                lint_cmd('test', 'lint', ['--no-color', fn])

            # The dennis version will change and the temp directory
            # we're using will change, so we're lenient when checking
            # the first two lines.
            output = stdout.getvalue()
            line, output = output.split('\n', 1)
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
        stdout = StringIO()
        stderr = StringIO()
        with redirect(stdout=stdout, stderr=stderr):
            ret = lint_cmd('test', 'lint', ['foo'])

        eq_(ret, 1)
        assert 'No files to work on.' in stderr.getvalue()

    def test_file_not_exists(self):
        with tempdir() as dir_:
            fn = os.path.join(dir_, 'messages.po')
            stdout = StringIO()
            stderr = StringIO()
            with redirect(stdout=stdout, stderr=stderr):
                ret = lint_cmd('test', 'lint', [fn])

            eq_(ret, 1)
            assert (
                'IOError' in stderr.getvalue()
                or 'OSError' in stderr.getvalue()
            )
            assert 'does not exist' in stderr.getvalue()


class LinterTest(TestCase):
    def test_linter(self):
        pofile = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        linter = Linter(['pysprintf', 'pyformat'], ['E201', 'W202'])
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

        linter = Linter(['pysprintf', 'pyformat'], ['E201', 'W202'])
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

        linter = Linter(['pysprintf', 'pyformat'], ['E201', 'W202'])
        msgs = linter.verify_file(pofile)

        # There were no translated strings, so nothing to lint.
        eq_(len(msgs), 0)


def build_linted_entry(po_data):
    po = polib.pofile(build_po_string(po_data))
    poentry = list(po)[0]
    return LintedEntry(poentry)


class LintRuleTestCase(TestCase):
    vartok = VariableTokenizer(['pysprintf', 'pyformat'])


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
    # non-pysprintf situations.


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
