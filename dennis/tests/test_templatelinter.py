import os
from unittest import TestCase

from nose.tools import eq_
import polib

from dennis.cmdline import linttemplate_cmd
from dennis.minisix import StringIO
from dennis.templatelinter import (
    HardToReadNamesTLR,
    OneCharNamesTLR,
    MultipleUnnamedVarsTLR,
    TemplateLinter,
    LintedEntry,
)
from dennis.tools import VariableTokenizer
from dennis.tests import build_po_string, redirect, tempdir


class LinTemplateCmdTest(TestCase):
    def test_empty(self):
        stdout = StringIO()
        with redirect(stdout=stdout):
            linttemplate_cmd('test', 'linttemplate', [])

    def test_basic(self):
        with tempdir() as dir_:
            pofile = build_po_string(
                '#: foo/foo.py:5\n'
                'msgid "Foo: %(l)s"\n'
                'msgstr ""\n')

            fn = os.path.join(dir_, 'messages.pot')
            with open(fn, 'w') as fp:
                fp.write(pofile)

            stdout = StringIO()
            stderr = StringIO()
            with redirect(stdout=stdout, stderr=stderr):
                linttemplate_cmd('test', 'linttemplate', [fn])

            assert '>>> Working on:' in stdout.getvalue()

    def test_no_files_to_work_on(self):
        stdout = StringIO()
        stderr = StringIO()
        with redirect(stdout=stdout, stderr=stderr):
            ret = linttemplate_cmd('test', 'linttemplate', ['foo'])

        eq_(ret, 1)
        assert 'No files to work on.' in stderr.getvalue()

    def test_file_not_exists(self):
        with tempdir() as dir_:
            fn = os.path.join(dir_, 'messages.pot')
            stdout = StringIO()
            stderr = StringIO()
            with redirect(stdout=stdout, stderr=stderr):
                ret = linttemplate_cmd('test', 'linttemplate', [fn])

            eq_(ret, 1)
            assert (
                'IOError' in stderr.getvalue()
                or 'OSError' in stderr.getvalue()
            )
            assert 'does not exist' in stderr.getvalue()


class TemplateLinterTest(TestCase):
    def test_linter(self):
        pofile = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr ""\n')

        linter = TemplateLinter(['pysprintf', 'pyformat'], ['W500'])
        results = linter.verify_file(pofile)

        # This should give us one linted entry with no errors
        # and no warnings in it.
        eq_(len(results), 1)
        eq_(len(results[0].warnings), 0)


def build_linted_entry(po_data):
    po = polib.pofile(build_po_string(po_data))
    poentry = list(po)[0]
    return LintedEntry(poentry)


class TLRTestCase(TestCase):
    vartok = VariableTokenizer(['pysprintf', 'pyformat'])


class HardToReadNamesTLRTestCase(TLRTestCase):
    lintrule = HardToReadNamesTLR()

    def test_hard_to_read_names(self):
        for c in ('o', 'O', '0', 'l', '1'):
            linted_entry = build_linted_entry(
                '#: foo/foo.py:5\n'
                'msgid "Foo: %(' + c + ')s"\n'
                'msgstr ""\n')

            self.lintrule.lint(self.vartok, linted_entry)

            eq_(len(linted_entry.warnings), 1)

            linted_entry = build_linted_entry(
                '#: foo/foo.py:5\n'
                'msgid "Foo: {' + c + '}"\n'
                'msgstr ""\n')

            self.lintrule.lint(self.vartok, linted_entry)

            eq_(len(linted_entry.warnings), 1)


class MultipleUnnamedVarsTLRTestCase(TLRTestCase):
    lintrule = MultipleUnnamedVarsTLR()

    def test_multi_vars_no_name(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: %s %s"\n'
            'msgstr ""\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {} {}"\n'
            'msgstr ""\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)


class OneCharNamesTLRTestCase(TLRTestCase):
    lintrule = OneCharNamesTLR()

    def test_one_character_names(self):
        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: %(c)s"\n'
            'msgstr ""\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)

        linted_entry = build_linted_entry(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {c}"\n'
            'msgstr ""\n')

        self.lintrule.lint(self.vartok, linted_entry)

        eq_(len(linted_entry.warnings), 1)
