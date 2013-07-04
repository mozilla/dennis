try:
    from blessings import Terminal
except ImportError:
    class MockBlessedThing(object):
        def __call__(self, s):
            return s

        def __str__(self):
            return ''

        def __repr__(self):
            return ''

        def __unicode__(self):
            return ''

    class Terminal(object):
        def __getattr__(self, attr, default=None):
            return MockBlessedThing()

import re


class PythonVarType(object):
    """Python %(foo)s and {foo} syntax"""
    name = 'python'
    regexp = (
        r'(?:%(?:[(]\S+?[)])?[#0+-]?[\.\d\*]*[hlL]?[diouxXeEfFgGcrs%])'
        r'|'
        r'(?:\{\S+?\})'
    )


VAR_TYPES = dict(
    (var_class.name, (var_class, var_class.__doc__))
    for name, var_class in globals().items()
    if name.endswith('VarType')
)


class UnknownVarType(Exception):
    pass


def get_types():
    return ', '.join(
        [
            '{name} ({desc})'.format(name=name, desc=data[1])
            for name, data in sorted(VAR_TYPES.items())
        ]
    )


class VariableTokenizer(object):
    def __init__(self, var_types=None):
        """
        :arg var_types: List of types.

            If None, creates a VariableTokenizer that tokenizes on all
            types of variables. Otherwise just recognizes the listed
            types.

        """
        if var_types is None:
            var_types = VAR_TYPES.keys()

        # Convert names to classes
        self.var_types = []

        for v in var_types:
            try:
                self.var_types.append(VAR_TYPES[v][0])
            except KeyError:
                raise UnknownVarType(
                    '{0} is not a known variable type'.format(v))

        # Generate variable regexp
        self.var_re = re.compile(
            r'(' +
            '|'.join([vt.regexp for vt in self.var_types]) +
            r')'
        )

    def tokenize(self, text):
        """Breaks s into strings and Python formatting tokens

        This preserves whitespace.

        :arg text: the string to tokenize

        :returns: list of tokens---every even one is a Python formatting
            token

        """
        return self.var_re.split(text)

    def extract_tokens(self, text):
        """Returns sorted tuple of tokens in the text"""
        try:
            tokens = [token for token in self.var_re.findall(text)]
            return tuple(sorted(tokens))
        except TypeError:
            print 'TYPEERROR', repr(text)

    def is_token(self, text):
        return self.var_re.match(text) is not None
