from dennis.tools import (
    VariableTokenizer,
    PythonFormat,
    PythonBraceFormat,
    parse_dennis_note
)

from nose.tools import eq_


def test_python_tokenizing():
    vartok = VariableTokenizer(['python-format', 'python-brace-format'])
    data = [
        ('Hello %s', ['Hello ', '%s', '']),
        ('Hello %(username)s', ['Hello ', '%(username)s', '']),
        ('Hello %(user)s%(name)s', ['Hello ', '%(user)s', '', '%(name)s', '']),
        ('Hello {username}', ['Hello ', '{username}', '']),
        ('Hello {user}{name}', ['Hello ', '{user}', '', '{name}', '']),
        ('Products and Services', ['Products and Services']),
    ]

    for text, expected in data:
        eq_(vartok.tokenize(text), expected)


def test_pythonbraceformat():
    v = PythonBraceFormat()

    eq_(v.extract_variable_name('{}'), '')
    eq_(v.extract_variable_name('{0}'), '0')
    eq_(v.extract_variable_name('{abc}'), 'abc')
    eq_(v.extract_variable_name('{abc.def}'), 'abc.def')
    eq_(v.extract_variable_name('{abc[0]}'), 'abc[0]')
    eq_(v.extract_variable_name('{abc!s}'), 'abc')  # conversion
    eq_(v.extract_variable_name('{abc: >16}'), 'abc')  # format_spec


def test_pythonformat():
    v = PythonFormat()

    eq_(v.extract_variable_name('%s'), '')
    eq_(v.extract_variable_name('%d'), '')
    eq_(v.extract_variable_name('%.2f'), '')

    eq_(v.extract_variable_name('%(foo)s'), 'foo')


def test_parse_dennis_note():
    data = [
        ('', []),
        ('Foo', []),
        ('Foo bar', []),
        ('dennis-ignore', []),
        ('dennis-ignore: *', '*'),
        ('dennis-ignore: E101', ['E101']),
        ('dennis-ignore: E101, E102', ['E101']),
        ('dennis-ignore: E101,E102', ['E101', 'E102']),
        ('localizers ignore this: dennis-ignore: E101,E102', ['E101', 'E102'])
    ]

    for text, expected in data:
        eq_(parse_dennis_note(text), expected)
