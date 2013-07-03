from nose.tools import eq_

from dennis.linter import compare_lists


def test_compare_lists():
    tests = [
        ([], [], ([], [])),
        ([1, 2, 3], [3, 4, 5], ([1, 2], [4, 5])),
    ]

    for list_a, list_b, expected in tests:
        eq_(compare_lists(list_a, list_b), expected)
