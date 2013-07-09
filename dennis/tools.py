try:
    from blessings import Terminal
except ImportError:
    class MockBlessedThing(object):
        def __call__(self, s):
            return s

    class Terminal(object):
        def __getattr__(self, attr, default=None):
            return MockBlessedThing()

import optparse
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
    """Return name and description for all types"""
    return [(name, data[1]) for name, data in sorted(VAR_TYPES.items())]


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


class BetterArgumentParser(optparse.OptionParser):
    """OptionParser that allows for additional help sections

    OptionParser can take a description and an epilog, but it
    textwraps them which destroys all formatting. This allows us to
    have additional sections after the epilog which can maintain
    formatting.

    When creating the parser, pass in a ``sections`` kw argument with
    a list of tuples of the form ``(text, boolean)``. The text is the
    section text. The boolean indicates whether or not to textwrap the
    text.

    Example::

        BetterArgumentParser(usage='usage: %prog blah blah', version='1.0',
            sections=[
                ('List\nof\nthings', False),  # Maintains format
                ('List\nof\nthings', True),   # Textwrapped
            ])

    """
    def __init__(self, *args, **kw):
        if 'sections' in kw:
            self.sections = kw.pop('sections')
        else:
            self.sections = []
        optparse.OptionParser.__init__(self, *args, **kw)

    def format_help(self, formatter=None):
        help_text = optparse.OptionParser.format_help(self, formatter)
        for (section, raw) in self.sections:
            if raw:
                help_text += section
            else:
                help_text += self._format_text(section)
            help_text += '\n'

        return help_text
