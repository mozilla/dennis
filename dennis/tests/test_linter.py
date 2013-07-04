from unittest import TestCase

from nose.tools import eq_

from dennis.linter import _compare_lists, _verify


def test_compare_lists():
    tests = [
        ([], [], ([], [])),
        ([1, 2, 3], [3, 4, 5], ([1, 2], [4, 5])),
    ]

    for list_a, list_b, expected in tests:
        eq_(_compare_lists(list_a, list_b), expected)
