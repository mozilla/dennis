from unittest import TestCase

from nose.tools import eq_
import polib

from dennis.linter import (
    MalformedNoTypeLintRule,
    MalformedMissingRightBraceLintRule,
    MalformedMissingLeftBraceLintRule,
    MissingVarsLintRule,
    InvalidVarsLintRule,
    LintedEntry,
    Linter
)
from dennis.tools import VariableTokenizer
from dennis.tests import build_po_string


class LinterTest(TestCase):
    def test_linter(self):
        pofile = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        linter = Linter(['pysprintf', 'pyformat'], ['E201', 'W202'])
        results = linter.verify_file(pofile)

        # This should give us one linted entry with no errors
        # and no warnings in it.
        eq_(len(results), 1)
        eq_(len(results[0].errors), 0)
        eq_(len(results[0].warnings), 0)

    def test_linter_fuzzy_strings(self):
        pofile = build_po_string(
            '#, fuzzy\n'
            '#~ msgid "Most Recent Message"\n'
            '#~ msgid_plural "Last %(count)s Messages"\n'
            '#~ msgstr[0] "Les {count} derniers messages"\n'
            '#~ msgstr[1] "Les {count} derniers messages"\n')

        linter = Linter(['pysprintf', 'pyformat'], ['E201', 'W202'])
        results = linter.verify_file(pofile)

        # There were no non-fuzzy strings, so nothing to lint.
        eq_(len(results), 0)

    def test_linter_untranslated_strings(self):
        pofile = build_po_string(
            '#, fuzzy\n'
            '#~ msgid "Most Recent Message"\n'
            '#~ msgid_plural "Last %(count)s Messages"\n'
            '#~ msgstr[0] ""\n'
            '#~ msgstr[1] ""\n')

        linter = Linter(['pysprintf', 'pyformat'], ['E201', 'W202'])
        results = linter.verify_file(pofile)

        # There were no translated strings, so nothing to lint.
        eq_(len(results), 0)


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

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

    def test_python_var_with_space(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(count)s view"\n'
            'msgid_plural "%(count)s views"\n'
            'msgstr[0] "%(count) zoo"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'type missing: %(count)')

    def test_python_var_end_of_line(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(count)s"\n'
            'msgid_plural "%(count)s"\n'
            'msgstr[0] "%(count)"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'type missing: %(count)')

    def test_python_var_not_malformed(self):
        """This used to be a false positive"""
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(stars)s by %(user)s on %(date)s (%(locale)s)"\n'
            'msgstr "%(stars)s de %(user)s el %(date)s (%(locale)s)"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)

    # FIXME - test to make sure it doesn't do anything for
    # non-pysprintf situations.


class MalformedMissingRightBraceLintRuleTest(LintRuleTestCase):
    lintrule = MalformedMissingRightBraceLintRule()

    def test_python_var_missing_right_curly_brace(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{foo} bar is the best thing ever"\n'
            'msgstr "{foo) bar is the best thing ever"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'missing right curly-brace: {foo) bar is the best thing ever')

        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{foo}"\n'
            'msgstr "{foo"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'missing right curly-brace: {foo')

    def test_python_var_missing_right_curly_brace_two_vars(self):
        # Test right-most one
        linted_entry = build_linted_entry(
            'msgid "Value for key \\"{0}\\" exceeds the length of {1}"\n'
            'msgstr "Valor para la clave \\"{0}\\" excede el tamano de {1]"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'missing right curly-brace: {1]')

        # Test left-most one
        linted_entry = build_linted_entry(
            'msgid "Value for key \\"{0}\\" exceeds the length of {1}"\n'
            'msgstr "Valor para la clave \\"{0]\\" excede el tamano de {1}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'missing right curly-brace: {0]" excede el tamano de {')


class MalformedMissingLeftBraceLintRuleTest(LintRuleTestCase):
    lintrule = MalformedMissingLeftBraceLintRule()

    def test_python_var_missing_left_curly_brace(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{product} Support Forum"\n'
            'msgstr "product}-Hilfeforum"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'missing left curly-brace: product}')

        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{q} | {product} Support Forum"\n'
            'msgstr "{q} | product}-Hilfeforum"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'missing left curly-brace: } | product}')


class MissingVarsLintRuleTest(LintRuleTestCase):
    lintrule = MissingVarsLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

    def test_missing(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
        eq_(linted_entry.warnings[0][2],
            'missing variables: {foo}')
        eq_(len(linted_entry.errors), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo} {bar} {baz}"\n'
            'msgstr "Oof: {foo}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
        eq_(linted_entry.warnings[0][2],
            'missing variables: {bar}, {baz}')
        eq_(len(linted_entry.errors), 0)

    def test_complex(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {bar} {baz}"\n'
            'msgstr "Oof: {foo} {bar}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
        eq_(linted_entry.warnings[0][2],
            'missing variables: {baz}')
        eq_(len(linted_entry.errors), 0)

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

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)

    def test_double_percent(self):
        # Double-percent shouldn't be picked up as a variable.
        # Issue #28.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "50% of the traffic"\n'
            'msgstr "more than 50%% of the traffic"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)

    def test_urlencoded_urls(self):
        # urlencoding uses % and that shouldn't get picked up
        # as variables.
        # Issue #27.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "OMG! Best url is http://example.com/foo"\n'
            'msgstr "http://example.com/foo%20%E5%B4%A9%E6%BA%83 is best"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)


class InvalidVarsLintRuleTest(LintRuleTestCase):
    lintrule = InvalidVarsLintRule()

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

    def test_invalid(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof: {foo}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'invalid variables: {foo}')

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo} {bar} {baz}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'invalid variables: {bar}, {baz}')

    def test_complex(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {bar} {baz}"\n'
            'msgstr "Oof: {foo} {bar}"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
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

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)

    def test_double_percent(self):
        # Double-percent shouldn't be picked up as a variable.
        # Issue #28.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "50% of the traffic"\n'
            'msgstr "more than 50%% of the traffic"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)

    def test_urlencoded_urls(self):
        # urlencoding uses % and that shouldn't get picked up
        # as variables.
        # Issue #27.
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "OMG! Best url is http://example.com/foo"\n'
            'msgstr "http://example.com/foo%20%E5%B4%A9%E6%BA%83 is best"\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)
