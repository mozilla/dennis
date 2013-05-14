import re


INTERP_RE = re.compile(
    r'('
    r'(?:%(?:[(]\S+?[)])?[#0+-]?[\.\d\*]*[hlL]?[diouxXeEfFgGcrs%])'
    r'|'
    r'(?:\{\S+?\})'
    r')')


def tokenize(s):
    """Breaks s into strings and Python formatting tokens

    This preserves whitespace.

    :arg s: the string to tokenize

    :returns: list of tokens---every even one is a Python formatting
        token

    """
    return INTERP_RE.split(s)


def extract_tokens(text):
    """Returns sorted tuple of tokens in the text"""
    try:
        tokens = [token for token in INTERP_RE.findall(text)]
        return tuple(sorted(tokens))
    except TypeError:
        print 'TYPEERROR', repr(text)


def is_token(text):
    return INTERP_RE.match(text) is not None
