import HTMLParser
import polib
import re
import string

from dennis.tools import VariableTokenizer


DEBUG = False


def debug(*args):
    if DEBUG:
        print ' '.join([str(arg) for arg in args])


class Token(object):
    def __init__(self, s, type='text', mutable=True):
        self.s = s
        self.type = type
        self.mutable = mutable

    def __str__(self):
        return self.s.encode('utf-8')

    def __unicode__(self):
        return self.s

    def __repr__(self):
        return '<{0} {1}>'.format(self.type, self.s.encode('utf-8'))

    def __eq__(self, token):
        return (
            self.s == token.s
            and self.mutable == token.mutable
            and self.type == token.type)


class Transform(object):
    name = ''
    desc = ''

    def transform(self, vartok, token_stream):
        """Takes a token stream and returns a token stream

        :arg vartok: the variable tokenizer to use for tokenizing
            on variable tokens
        :arg token_stream: the input token stream this transform
            is operating on

        :return: iterable of transformed tokens

        """
        raise NotImplemented


class EmptyTransform(Transform):
    name = 'empty'
    desc = 'Returns empty strings.'

    def transform(self, vartok, token_stream):
        return [Token('')]


class XXXTransform(Transform):
    name = 'xxx'
    desc = 'Adds xxx before and after lines in a string.'

    def transform(self, vartok, token_stream):
        new_tokens = []
        for token in token_stream:
            if not token.mutable:
                new_tokens.append(token)
                continue

            new_s = []
            s = token.s
            for line in s.splitlines(True):
                line, ending = self.split_ending(line)
                line = u'xxx' + line + u'xxx' + ending
                new_s.append(line)

            new_tokens.append(Token(''.join(new_s)))

        return new_tokens

    def split_ending(self, s):
        ending = []
        while s:
            if s[-1] in string.whitespace:
                ending.insert(0, s[-1])
                s = s[:-1]
            else:
                return s, u''.join(ending)

        return u'', ''.join(ending)


class HahaTransform(Transform):
    name = 'haha'
    desc = 'Adds haha! before sentences in a string.'


    def transform(self, vartok, token_stream):
        haha = u'Haha\u2757'

        new_tokens = []
        for token in token_stream:
            if not token.mutable:
                new_tokens.append(token)
                continue

            new_s = [haha + u' ']

            for i, c in enumerate(token.s):
                if c in ('.!?'):
                    try:
                        if token.s[i+1] == ' ':
                            new_s.append(c)
                            new_s.append(u' ')
                            new_s.append(haha)
                            continue
                    except IndexError:
                        pass
                if c == '\n':
                    new_s.append(c)
                    new_s.append(haha)
                    new_s.append(u' ')
                    continue

                new_s.append(c)

            new_tokens.append(Token(''.join(new_s)))

        return new_tokens

    def split_ending(self, s):
        ending = []
        while s:
            if s[-1] in string.whitespace:
                ending.insert(0, s[-1])
                s = s[:-1]
            else:
                return s, u''.join(ending)

        return u'', ''.join(ending)


class AngleQuoteTransform(XXXTransform):
    name = 'anglequote'
    desc = 'Encloses string in unicode angle quotes.'

    def transform(self, vartok, token_stream):
        new_tokens = []
        for token in token_stream:
            if not token.mutable:
                new_tokens.append(token)
                continue

            s, ending = self.split_ending(token.s)
            s = u'\u00ab' + s + u'\u00bb' + ending
            new_tokens.append(Token(s))

        return new_tokens


class ShoutyTransform(Transform):
    name = 'shouty'
    desc = 'Translates into all caps.'

    def transform(self, vartok, token_stream):
        new_tokens = []
        for token in token_stream:
            if not token.mutable:
                new_tokens.append(token)
                continue

            new_tokens.append(Token(token.s.upper()))

        return new_tokens


class RedactedTransform(Transform):
    name = 'redacted'
    desc = 'Redacts everything'

    def transform(self, vartok, token_stream):
        new_tokens = []
        for token in token_stream:
            if not token.mutable:
                new_tokens.append(token)
                continue

            new_s = [
                ('X' if c in string.ascii_uppercase else
                 ('x' if c in string.ascii_lowercase else c))
                for c in token.s
            ]
            new_tokens.append(Token(u''.join(new_s)))

        return new_tokens


class PirateTransform(Transform):
    name = 'pirate'
    desc = 'Translates text into Pirate!'

    def transform(self, vartok, token_stream):
        new_tokens = []

        for token in token_stream:
            if not token.mutable:
                new_tokens.append(token)
                continue

            out = u''
            for i, part in enumerate(vartok.tokenize(token.s)):
                if i % 2 == 0:
                    out += self.pirate_transform(part)
                else:
                    out += part

            # Add color which causes every string to be longer, but
            # only if the string isn't entirely whitespace.
            if not self.is_whitespace(out):
                s, ending = self.split_ending(out)
                out = (s + u' ' + self.COLOR[len(out) % len(self.COLOR)] +
                       ending)

                # This guarantees that every string has at least one
                # unicode charater
                if '!' not in out:
                    out = out + u'!'

                # Replace all ! with related unicode character.
                out = out.replace(u'!', u'\u2757')

            new_tokens.append(Token(out))

        return new_tokens

    COLOR = [
        u'arr!',
        u'arrRRr!',
        u'arrRRRrrr!',
        u'matey!',
        u'me mateys!',
        u'ahoy!',
        u'aye!',
        u'ye scalleywag!',
        u'cap\'n!',
        u'yo-ho-ho!',
        u'shiver me timbers!',
        u'ye landlubbers!',
        u'prepare to be boarded!',
        ]

    def wc(self, c):
        return c == '\'' or c in string.letters

    def nwc(self, c):
        return not self.wc(c)

    def is_whitespace(self, s):
        return re.match('^\\s*$', s) is not None

    # List of transform rules. The tuples have:
    #
    # * in word
    # * not in word
    # * match string
    # * word character
    # * not word character
    # * replacement string
    #
    # See the transform code for details.
    TRANSFORM = (
        # INW?, NIW?, match, WC?, NW?, replacement
        # Anti-replacements: need these so that we make sure these words
        # don't get screwed up by later rules.
        (False, True, 'need', False, True, 'need'),
        (False, True, 'Need', False, True, 'Need'),

        # Replace entire words
        (False, True, 'add-on', False, True, 'bilge rat'),
        (False, True, 'add-ons', False, True, 'bilge rats'),
        (False, True, 'are', False, True, 'bee'),
        (False, True, 'browser', False, True, 'corsairr'),
        (False, True, 'for', False, True, 'fer'),
        (False, True, 'Hi', False, True, 'H\'ello'),
        (False, True, 'my', False, True, 'me'),
        (False, True, 'no', False, True, 'nay'),
        (False, True, 'of', False, True, 'o\''),
        (False, True, 'over', False, True, 'o\'err'),
        (False, True, 'plugin', False, True, 'mug o\' grog'),
        (False, True, 'plugins', False, True, 'mugs o\' grog'),
        (False, True, 'program', False, True, 'Jolly Rogerr'),
        (False, True, 'the', False, True, 'th\''),
        (False, True, 'there', False, True, 'tharr'),
        (False, True, 'want', False, True, 'wants'),
        (False, True, 'where', False, True, '\'erre'),
        (False, True, 'with', False, True, 'wit\''),
        (False, True, 'yes', False, True, 'aye'),
        (False, True, 'you', False, True, 'ye\''),
        (False, True, 'You', False, True, 'Ye\''),
        (False, True, 'your', False, True, 'yerr'),
        (False, True, 'Your', False, True, 'Yerr'),

        # Prefixes
        (False, True, 'hel', True, False, '\'el'),
        (False, True, 'Hel', True, False, '\'el'),

        # Mid-word
        (True, False, 'er', True, False, 'arr'),

        # Suffixes
        (True, False, 'a', False, True, 'ar'),
        (True, False, 'ed', False, True, '\'d'),
        (True, False, 'ing', False, True, 'in\''),
        (True, False, 'ort', False, True, 'arrt'),
        (True, False, 'r', False, True, 'rr'),
        (True, False, 'w', False, True, 'ww'),
    )

    def split_ending(self, s):
        ending = []
        while s:
            if s[-1] in '.,":;?!\n':
                ending.insert(0, s[-1])
                s = s[:-1]
            else:
                return s, u''.join(ending)

        return u'', ''.join(ending)

    def pirate_transform(self, s):
        """Transforms a token into Pirate.

        :arg s: The token to transform.

        :returns: Piratized token

        """
        out = []

        in_word = False  # in a word?

        # TODO: This is awful--better to do a real lexer
        while s:
            if s.startswith(('.', '!', '?')):
                in_word = False
                out.append(s[0])
                s = s[1:]
                continue

            debug(s, in_word)

            for mem in self.TRANSFORM:
                # Match inside a word? (Not a prefix.)
                if in_word and not mem[0]:
                    debug(mem, 'not in word')
                    continue

                # Not match inside a word? (Prefix.)
                if not in_word and not mem[1]:
                    debug(mem, 'in word')
                    continue

                if not s.startswith(mem[2]):
                    debug(mem, 'not match')
                    continue

                # Check the character after the match to see if it's a
                # word character and whether this match covers that.
                try:
                     # WC: word character
                    if mem[3] and not self.wc(s[len(mem[2])]):
                        debug(mem, 'not wc')
                        continue
                except IndexError:
                    # We don't count EOS as a word character.
                    if mem[3]:
                        debug(mem, 'not wc')
                        continue

                # Check the character after the match to see if it's not a
                # word character and whether this match covers that.
                try:
                    # NW: not word character
                    if mem[4] and not self.nwc(s[len(mem[2])]):
                        debug(mem, 'wc')
                        continue
                except IndexError:
                    # We count EOS as a non-word character.
                    if not mem[4]:
                        debug(mem, 'wc')
                        continue

                out.append(mem[5])
                s = s[len(mem[2]):]
                in_word = True
                break

            else:
                in_word = self.wc(s[0])
                out.append(s[0])
                s = s[1:]

        return u''.join(out)


class HTMLExtractorTransform(HTMLParser.HTMLParser, Transform):
    name = 'html'
    desc = 'Tokenizes HTML bits so only text is translated.'

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.new_tokens = []

    def transform(self, vartok, token_stream):
        out = []

        for token in token_stream:
            if not token.mutable:
                out.append(token)
                continue

            if token.s:
                self.feed(token.s)
                out.extend(self.new_tokens)
                self.new_tokens = []
            else:
                out.append(token)

        return out

    def handle_starttag(self, tag, attrs, closed=False):
        # We want to translate alt and title values, but that's
        # it. So this gets a little goofy looking token-wise.

        s = '<' + tag
        for name, val in attrs:
            s += ' '
            s += name
            s += '="'

            if name in ['alt', 'title']:
                self.new_tokens.append(Token(s, 'html', False))
                self.new_tokens.append(Token(val))
                s = ''
            else:
                s += val
            s += '"'
        if closed:
            s += ' /'
        s += '>'

        if s:
            self.new_tokens.append(Token(s, 'html', False))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        self.new_tokens.append(Token('</' + tag + '>', 'html', False))

    def handle_data(self, data):
        self.new_tokens.append(Token(data))

    def handle_charref(self, name):
        self.new_tokens.append(Token('&#' + name + ';', 'html', False))

    def handle_entityref(self, name):
        self.new_tokens.append(Token('&' + name + ';', 'html', False))


def get_available_pipeline_parts():
    pipeline_parts = {}

    for name, thing in globals().items():
        if (name.endswith('Transform')
            and issubclass(thing, Transform)
            and thing.name):
            pipeline_parts[thing.name] = thing

    return pipeline_parts


class InvalidPipeline(Exception):
    pass


def convert_pipeline(pipeline_spec):
    pipeline_parts = get_available_pipeline_parts()

    try:
        pipeline = [pipeline_parts[part] for part in pipeline_spec]
    except KeyError:
        raise InvalidPipeline(pipeline_spec)

    return pipeline


class Translator(object):
    def __init__(self, variable_formats, pipeline_spec):
        self.vartok = VariableTokenizer(variable_formats)
        self.pipeline_spec = pipeline_spec
        self.pipeline = convert_pipeline(self.pipeline_spec)

    def translate_string(self, s):
        # Create the initial token
        tokens = [Token(s)]

        # Pass the token list through the pipeline
        for part_class in self.pipeline:
            part = part_class()
            tokens = part.transform(self.vartok, tokens)

        # Join all the bits together
        return u''.join([token.s for token in tokens])

    def translate_file(self, fname):
        po = polib.pofile(fname)

        # FIXME - This might be a bit goofy
        po.metadata['Language'] = ",".join(self.pipeline_spec)
        po.metadata['Plural-Forms'] = 'nplurals=2; plural= n != 1'
        po.metadata['Content-Type'] = 'text/plain; charset=UTF-8'
        count = 0
        for entry in po:
            if entry.msgid_plural:
                entry.msgstr_plural['0'] = self.translate_string(
                    entry.msgid)
                entry.msgstr_plural['1'] = self.translate_string(
                    entry.msgid_plural)
            else:
                entry.msgstr = self.translate_string(entry.msgid)

            if 'fuzzy' in entry.flags:
                entry.flags.remove('fuzzy')  # clear the fuzzy flag
            count += 1
        print 'Munged %d messages in %s' % (count, fname)
        po.save()
