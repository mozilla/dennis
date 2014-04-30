from dennis.tools import VariableTokenizer

from nose.tools import eq_


def test_python_tokenizing():
    vartok = VariableTokenizer(['pysprintf', 'pyformat'])
    for string, expected in [
        ('Hello %s', ['Hello ', '%s', '']),
        ('Hello %(username)s', ['Hello ', '%(username)s', '']),
        ('Hello %(user)s%(name)s', ['Hello ', '%(user)s', '', '%(name)s', '']),
        ('Hello {username}', ['Hello ', '{username}', '']),
        ('Hello {user}{name}', ['Hello ', '{user}', '', '{name}', '']),
        ('Products and Services', ['Products and Services']),
        ]:
        eq_(vartok.tokenize(string), expected)
