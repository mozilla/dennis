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


class Var(object):
    """Variable base class"""
    name = ''
    desc = ''
    regexp = ''
    malformed_regexp = ''


class PythonVar(Var):
    name = 'python'
    desc = 'Python %(foo)s and {foo} syntax'
    regexp = (
        # %s and %(foo)s
        r'(?:%(?:[(]\S+?[)])?[#0+-]?[\.\d\*]*[hlL]?[diouxXeEfFgGcrs%])'
        r'|'
        # {foo}
        r'(?:\{\S+?\})'
    )
    malformed_regexp = (
        # %(count) with no type at end
        r'(?:%[(]\S+?[)](?:\s|$))'
        r'|'
        # %{foo with no end curly brace
        r'(?:\{[^\}]+$)'
    )


def get_available_vars():
    return dict(
        (thing.name, thing)
        for name, thing in globals().items()
        if (name.endswith('Var')
            and issubclass(thing, Var)
            and thing.name)
    )


class UnknownVar(Exception):
    pass


class VariableTokenizer(object):
    def __init__(self, vars_=None):
        """
        :arg vars_: List of variable formats

            If None, creates a VariableTokenizer that tokenizes on all
            types of variables. Otherwise just recognizes the listed
            types.

        """
        all_vars = get_available_vars()

        if vars_ is None:
            vars_ = all_vars.keys()

        # Convert names to classes
        self.vars_ = []

        for v in vars_:
            try:
                self.vars_.append(all_vars[v])
            except KeyError:
                raise UnknownVar(
                    '{0} is not a known variable type'.format(v))

        # Generate variable regexp
        self.vars_re = re.compile(
            r'(' +
            '|'.join([vt.regexp for vt in self.vars_]) +
            r')'
        )

        # Generate malformed variable regexp
        self.malformed_vars_re = re.compile(
            r'(' +
            '|'.join([vt.malformed_regexp for vt in self.vars_]) +
            r')'
        )


    def tokenize(self, text):
        """Breaks s into strings and Python formatting tokens

        This preserves whitespace.

        :arg text: the string to tokenize

        :returns: list of tokens---every even one is a Python formatting
            token

        """
        return self.vars_re.split(text)

    def extract_tokens(self, text):
        """Returns sorted tuple of tokens in the text"""
        try:
            tokens = [token for token in self.vars_re.findall(text)]
            return tuple(sorted(tokens))
        except TypeError:
            print 'TYPEERROR', repr(text)

    def is_token(self, text):
        return self.vars_re.match(text) is not None


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
