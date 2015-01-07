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


class Format(object):
    """Variable format base class"""
    name = ''
    desc = ''
    regexp = ''

    identifier = None

    @classmethod
    def extract_variable_name(cls, text):
        raise NotImplemented


# http://www.gnu.org/software/gettext/manual/html_node/python_002dformat.html#python_002dformat
# https://docs.python.org/2/library/string.html#format-string-syntax
class PythonBraceFormat(Format):
    name = 'python-brace-format'
    desc = 'Python brace format (e.g. "{0}", "{foo}")'

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


# http://www.gnu.org/software/gettext/manual/html_node/python_002dformat.html#python_002dformat
# http://docs.python.org/2/library/stdtypes.html#string-formatting-operations
class PythonFormat(Format):
    name = 'python-format'
    desc = 'Python percent format (e.g. "%s", "%(foo)s")'

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


def get_available_formats():
    return dict(
        (thing.name, thing)
        for name, thing in globals().items()
        if (name.endswith('Format')
            and issubclass(thing, Format)
            and thing.name)
    )


class UnknownFormat(Exception):
    pass


class VariableTokenizer(object):
    def __init__(self, formats=None):
        """
        :arg formats: List of variable formats

            If None, creates a VariableTokenizer that tokenizes on all
            formats of variables. Otherwise just recognizes the listed
            formats.

        """
        all_formats = get_available_formats()

        if formats is None:
            formats = all_formats.keys()

        # Convert names to classes
        self.formats = []

        for fmt in formats:
            try:
                self.formats.append(all_formats[fmt])
            except KeyError:
                raise UnknownFormat(
                    '{0} is not a known variable format'.format(fmt))

        # Generate variable regexp
        self.vars_re = re.compile(
            r'(' +
            '|'.join([vt.regexp for vt in self.formats]) +
            r')'
        )

    def contains(self, fmt):
        """Does this tokenizer contain specified variable format?"""
        return fmt in [tok.name for tok in self.formats]

    def tokenize(self, text):
        """Breaks s into strings and Python variables

        This preserves whitespace.

        :arg text: the string to tokenize

        :returns: list of tokens---every even one is a Python variable

        """
        return self.vars_re.split(text)

    def extract_tokens(self, text, unique=True):
        """Returns the set of variable in the text"""
        try:
            tokens = self.vars_re.findall(text)
            if unique:
                tokens = set(tokens)
            return tokens
        except TypeError:
            print('TYPEERROR: {0}'.format(repr(text)))

    def is_token(self, text):
        """Is this text a variable?"""
        return self.vars_re.match(text) is not None

    def extract_variable_name(self, text):
        for fmt in self.formats:
            if re.compile(fmt.regexp).match(text):
                return fmt.extract_variable_name(text)


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

    fp = list(fp)
    entries = list(parsed_pofile)
    for i, poentry in enumerate(entries):
        # Grab the lines that make up the poentry.
        # Note: linenum is 1-based, so we convert it to 0-based.
        try:
            lines = fp[poentry.linenum-1:entries[i+1].linenum-1]
        except IndexError:
            lines = fp[poentry.linenum-1:]

        # Nix blank lines at the end.
        while lines and not lines[-1].strip():
            lines.pop()

        # Join them and voila!
        poentry.original = textclass('').join(lines)

    return parsed_pofile


def withlines(linenum, poentry_text):
    """Returns text with line numbers"""
    start = linenum
    new_text = []

    lines_with_nums = zip(range(start, start+100), poentry_text.splitlines())

    for line_no, line in lines_with_nums:
        new_text.append(textclass(line_no) + textclass(':') + textclass(line))

    return textclass('\n').join(new_text)
