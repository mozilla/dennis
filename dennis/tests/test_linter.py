from unittest import TestCase

from nose.tools import eq_

from dennis.linter import _compare_lists, Linter


def build_po_string(data):
    return (
        '#, fuzzy\n'
        'msgid ""\n'
        'msgstr ""\n'
        '"Project-Id-Version: foo\\n"\n'
        '"POT-Creation-Date: 2013-06-05 14:16-0700\\n"\n'
        '"PO-Revision-Date: 2010-04-26 18:00-0700\\n"\n'
        '"Last-Translator: Automatically generated\\n"\n'
        '"Language-Team: English\\n"\n'
        '"Language: \\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        '"X-Generator: Translate Toolkit 1.6.0\\n"\n\n'
        + data)


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
