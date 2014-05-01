from dennis.tools import VariableTokenizer, parse_dennis_note

from nose.tools import eq_


def test_python_tokenizing():
    vartok = VariableTokenizer(['pysprintf', 'pyformat'])
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
