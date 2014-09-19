import optparse
import re

from dennis.minisix import textclass


class _MockBlessedThing(textclass):
    def __call__(self, s):
        return s


class FauxTerminal(object):
    def __getattr__(self, attr, default=None):
        return _MockBlessedThing()


try:
    from blessings import Terminal
except ImportError:
    Terminal = FauxTerminal


class Var(object):
    """Variable base class"""
    name = ''
    desc = ''
    regexp = ''

    identifier = None

    @classmethod
    def extract_variable_name(cls, text):
        raise NotImplemented


# https://docs.python.org/2/library/string.html#format-string-syntax
class PythonFormatVar(Var):
    name = 'pyformat'
    desc = 'Python format string syntax (e.g. "{0}", "{foo}")'

    regexp = (
        # {foo}
        r'(?:\{\S*?\})'
    )

    identifier = re.compile(r'\{([^!:\}]*)')

    @classmethod
    def extract_variable_name(cls, text):
        identifier = cls.identifier.match(text)
        if identifier:
            return identifier.group(1)


# http://docs.python.org/2/library/stdtypes.html#string-formatting-operations
class PythonPercentVar(Var):
    name = 'pysprintf'
    desc = 'Python sprintf syntax (e.g. "%s", "%(foo)s")'

    regexp = (
        # %s and %(foo)s
        # Note: This doesn't support %E or %F because of problems
        # with false positives and urlencoding. Theoretically those
        # aren't getting used in gettext contexts anyhow.
        r'(?:%(?:[(]\S+?[)])?[#0+-]?[\.\d\*]*[hlL]?[diouxefGgcrs])'
    )

    identifier = re.compile(
        r'%'
        r'(?:' + r'\((\S+?)\)' + r')?'
        r'[#0+-]?[\.\d\*]*[hlL]?[diouxefGgcrs]'
    )

    @classmethod
    def extract_variable_name(cls, text):
        identifier = cls.identifier.match(text)
        if identifier:
            return identifier.group(1) or ''


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

    def contains(self, var_):
        """Does this tokenizer contain specified variable type?"""
        return var_ in [tok.name for tok in self.vars_]

    def tokenize(self, text):
        """Breaks s into strings and Python formatting tokens

        This preserves whitespace.

        :arg text: the string to tokenize

        :returns: list of tokens---every even one is a Python formatting
            token

        """
        return self.vars_re.split(text)

    def extract_tokens(self, text, unique=True):
        """Returns the set of variable tokens in the text"""
        try:
            tokens = self.vars_re.findall(text)
            if unique:
                tokens = set(tokens)
            return tokens
        except TypeError:
            print('TYPEERROR: {0}'.format(repr(text)))

    def is_token(self, text):
        """Is this text a variable token?"""
        return self.vars_re.match(text) is not None

    def extract_variable_name(self, text):
        for vt in self.vars_:
            if re.compile(vt.regexp).match(text):
                return vt.extract_variable_name(text)


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


def all_subclasses(cls):
    subc = cls.__subclasses__()
    for d in list(subc):
        subc.extend(all_subclasses(d))
    return subc


# Matches:
# "dennis-ignore: *" to skip all the rules
# "dennis-ignore: E201,..." to ignore specific rules
DENNIS_NOTE_RE = re.compile(r'dennis-ignore:\s+(\*|[EW0-9,]+)')


def parse_dennis_note(text):
    """Parses a dennis note and returns list of rules to skip"""
    if not text:
        return []

    match = DENNIS_NOTE_RE.search(text)
    if not match:
        return []

    match = match.group(1).strip()
    if match == '*':
        return '*'

    return [item for item in match.split(',') if item]


def parse_pofile(fn_or_string):
    """Parses a po file and attaches original poentry blocks

    When polib parses a pofile, it captures the line number of the
    start of the block, but doesn't capture the original string for
    the block. When you call str()/unicode() on the poentry, it
    "reassembles" the block with textwrapped lines, so it returns
    something substantially different than the original block. This is
    problematic if we want to print out the block with the line
    numbers--one for each line.

    So this wrapper captures the line numbers and original text for
    each block and attaches that to the parsed poentries in an
    attribute named "original" thus allowing us to print the original
    text with line numbers.

    """
    from polib import _is_file, detect_encoding, io, pofile

    # This parses the pofile
    parsed_pofile = pofile(fn_or_string)

    # Now we need to build a linenumber -> block hash so that we can
    # accurately print out what was in the pofile because polib will
    # reassembled what it parsed, but it's not the same.
    if _is_file(fn_or_string):
        enc = detect_encoding(fn_or_string, 'pofile')
        fp = io.open(fn_or_string, 'rt', encoding=enc)
    else:
        fp = fn_or_string.splitlines(True)

    linenum_to_block = {}
    block = []
    starti = None
    for i, line in enumerate(fp):
        if not line.strip() and block:
            # Empty line so we emit a block and reset starti
            linenum_to_block[starti+1] = textclass('').join(block)
            block = []
            starti = None
            continue

        if starti is None:
            starti = i
        block.append(line)

    if block:
        linenum_to_block[starti+1] = textclass('').join(block)

    # Go through the parsed_pofile list and "fix" all the POEntry
    # instances.
    for poentry in parsed_pofile:
        poentry.original = linenum_to_block[poentry.linenum]

    return parsed_pofile

def withlines(linenum, poentry_text):
    """Returns text with line numbers"""
    start = linenum
    new_text = []

    for line_no, line in zip(range(start, start+100), poentry_text.splitlines()):
        new_text.append(textclass(line_no) + textclass(':') + textclass(line))

    return textclass('\n').join(new_text)
