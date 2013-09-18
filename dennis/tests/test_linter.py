from unittest import TestCase

from nose.tools import eq_
import polib

from dennis.linter import (
    MalformedVarsLintRule, MismatchedVarsLintRule, LintedEntry, Linter)
from dennis.tools import VariableTokenizer
from dennis.tests import build_po_string


class LinterTest(TestCase):
    def test_linter(self):
        pofile = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        linter = Linter(['python'], ['mismatched'])
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

        linter = Linter(['python'], ['mismatched'])
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

        linter = Linter(['python'], ['mismatched'])
        results = linter.verify_file(pofile)

        # There were no translated strings, so nothing to lint.
        eq_(len(results), 0)


def build_linted_entry(po_data):
    po = polib.pofile(build_po_string(po_data))
    poentry = list(po)[0]
    return LintedEntry(poentry)


class LintRuleTestCase(TestCase):
    vartok = VariableTokenizer(['python'])


class MismatchedVarsLintRuleTests(LintRuleTestCase):
    mvlr = MismatchedVarsLintRule()

    def test_compare_lists(self):
        tests = [
            ([], [], ([], [])),
            ([1, 2, 3], [3, 4, 5], ([1, 2], [4, 5])),
        ]

        for list_a, list_b, expected in tests:
            eq_(MismatchedVarsLintRule.compare_lists(list_a, list_b),
                expected)

    def test_fine(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.errors), 0)
        eq_(len(linted_entry.warnings), 0)

    def test_missing(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
        eq_(linted_entry.warnings[0][2],
            'missing variables: {foo}')
        eq_(len(linted_entry.errors), 0)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo} {bar} {baz}"\n'
            'msgstr "Oof: {foo}"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
        eq_(linted_entry.warnings[0][2],
            'missing variables: {bar}, {baz}')
        eq_(len(linted_entry.errors), 0)

    def test_invalid(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof: {foo}"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'invalid variables: {foo}')

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo} {bar} {baz}"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'invalid variables: {bar}, {baz}')

    def test_complex(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {bar} {baz}"\n'
            'msgstr "Oof: {foo} {bar}"\n')

        self.mvlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
        eq_(linted_entry.warnings[0][2],
            'missing variables: {baz}')
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'invalid variables: {foo}')


class MalformedVarsLintRuleTests(LintRuleTestCase):
    mavlr = MalformedVarsLintRule()

    def test_python_var_with_space(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(count)s view"\n'
            'msgid_plural "%(count)s views"\n'
            'msgstr[0] "%(count) zoo"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'malformed variables: %(count)')

    def test_python_var_end_of_line(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(count)s"\n'
            'msgid_plural "%(count)s"\n'
            'msgstr[0] "%(count)"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'malformed variables: %(count)')

    def test_python_var_not_malformed(self):
        """This used to be a false positive"""
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "%(stars)s by %(user)s on %(date)s (%(locale)s)"\n'
            'msgstr "%(stars)s de %(user)s el %(date)s (%(locale)s)"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 0)

    def test_python_var_missing_right_curly_brace(self):
        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{foo} bar is the best thing ever"\n'
            'msgstr "{foo) bar is the best thing ever"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'malformed variables: {foo) bar is the best thing ever')

        linted_entry = build_linted_entry(
            '#: kitsune/questions/templates/questions/answers.html:56\n'
            'msgid "{foo}"\n'
            'msgstr "{foo"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'malformed variables: {foo')

    def test_python_var_missing_right_curly_brace_two_vars(self):
        # Test right-most one
        linted_entry = build_linted_entry(
            'msgid "Value for key \\"{0}\\" exceeds the length of {1}"\n'
            'msgstr "Valor para la clave \\"{0}\\" excede el tamano de {1]"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'malformed variables: {1]')

        # Test left-most one
        linted_entry = build_linted_entry(
            'msgid "Value for key \\"{0}\\" exceeds the length of {1}"\n'
            'msgstr "Valor para la clave \\"{0]\\" excede el tamano de {1}"\n')

        self.mavlr.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 0)
        eq_(len(linted_entry.errors), 1)
        eq_(linted_entry.errors[0][2],
            'malformed variables: {0]" excede el tamano de {')
