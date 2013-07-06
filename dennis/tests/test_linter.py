from unittest import TestCase

from nose.tools import eq_

from dennis.linter import _compare_lists, Linter
from dennis.tests import build_po_string


def test_compare_lists():
    tests = [
        ([], [], ([], [])),
        ([1, 2, 3], [3, 4, 5], ([1, 2], [4, 5])),
    ]

    for list_a, list_b, expected in tests:
        eq_(_compare_lists(list_a, list_b), expected)


class LinterTests(TestCase):
    def test_fine(self):
        po_string = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof"\n')

        linter = Linter(['python'])

        results = linter.verify_file(po_string)
        eq_(len(results), 1)
        eq_(results[0].missing, [])
        eq_(results[0].invalid, [])

        po_string = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo}"\n')

        linter = Linter(['python'])

        results = linter.verify_file(po_string)
        eq_(len(results), 1)
        eq_(results[0].missing, [])
        eq_(results[0].invalid, [])

    def test_missing(self):
        data = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof"\n')

        linter = Linter(['python'])

        results = linter.verify_file(data)
        eq_(len(results), 1)
        eq_(results[0].missing, [u'{foo}'])
        eq_(results[0].invalid, [])

        data = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo} {bar} {baz}"\n'
            'msgstr "Oof: {foo}"\n')

        linter = Linter(['python'])

        results = linter.verify_file(data)
        eq_(len(results), 1)
        eq_(results[0].missing, [u'{bar}', u'{baz}'])
        eq_(results[0].invalid, [])

    def test_invalid(self):
        data = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo"\n'
            'msgstr "Oof: {foo}"\n')

        linter = Linter(['python'])

        results = linter.verify_file(data)
        eq_(len(results), 1)
        eq_(results[0].missing, [])
        eq_(results[0].invalid, [u'{foo}'])

        data = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {foo}"\n'
            'msgstr "Oof: {foo} {bar} {baz}"\n')

        linter = Linter(['python'])

        results = linter.verify_file(data)
        eq_(len(results), 1)
        eq_(results[0].missing, [])
        eq_(results[0].invalid, [u'{bar}', u'{baz}'])

    def test_complex(self):
        data = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo: {bar} {baz}"\n'
            'msgstr "Oof: {foo} {bar}"\n')

        linter = Linter(['python'])

        results = linter.verify_file(data)
        eq_(len(results), 1)
        eq_(results[0].missing, [u'{baz}'])
        eq_(results[0].invalid, [u'{foo}'])
