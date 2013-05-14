from dennis.tools import tokenize

from nose.tools import eq_


def test_tokenize():
    for string, expected in [
        ('Hello %s', ['Hello ', '%s', '']),
        ('Hello %(username)s', ['Hello ', '%(username)s', '']),
        ('Hello %(user)s%(name)s', ['Hello ', '%(user)s', '', '%(name)s', '']),
        ('Hello {username}', ['Hello ', '{username}', '']),
        ('Hello {user}{name}', ['Hello ', '{user}', '', '{name}', '']),
        ('Products and Services', ['Products and Services']),
        ]:
        eq_(tokenize(string), expected)

    return 0
