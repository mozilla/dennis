import HTMLParser
import polib
import re
import string

from dennis.tools import tokenize


DEBUG = False


INTERP_RE = re.compile(
    r'((?:%(?:[(].+?[)])?[#0 +-]?[.\d*]*[hlL]?[diouxXeEfFgGcrs%])|(?:\{.+?\}))')


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


def debug(*args):
    if DEBUG:
        print ' '.join([str(arg) for arg in args])


def wc(c):
    return c == '\'' or c in string.letters


def nwc(c):
    return not wc(c)


def is_whitespace(s):
    return re.match('^\\s*$', s) != None


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


def pirate_transform(s):
    """Transforms a string into Pirate.

    :arg s: The string to transform.

    :returns: Pirated string.

    """
    old_s = s
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

        for mem in TRANSFORM:
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
                if mem[3] and not wc(s[len(mem[2])]):
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
                if mem[4] and not nwc(s[len(mem[2])]):
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
            in_word = wc(s[0])
            out.append(s[0])
            s = s[1:]

    return u''.join(out)


class HtmlAwareMessageMunger(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.s = ''

    def result(self):
        return self.s

    def xform(self, s):
        return pirate_transform(s)

    def handle_starttag(self, tag, attrs, closed=False):
        self.s += '<' + tag
        for name, val in attrs:
            self.s += ' '
            self.s += name
            self.s += '="'
            if name in ['alt', 'title']:
                self.s += self.xform(val)
            else:
                self.s += val
            self.s += '"'
        if closed:
            self.s += ' /'
        self.s += '>'

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        self.s += '</' + tag + '>'

    def handle_data(self, data):
        # We don't want to munge Python formatting tokens, so split on
        # them, keeping them in the list, then xform every other
        # token.
        toks = tokenize(data)

        for i, tok in enumerate(toks):
            if i % 2:
                self.s += tok
            else:
                self.s += self.xform(tok)

    def handle_charref(self, name):
        self.s += '&#' + name + ';'

    def handle_entityref(self, name):
        self.s += '&' + name + ';'


def split_ending(s):
    ending = []
    while s:
        if s[-1] in '.,":;?!':
            ending.insert(0, s[-1])
            s = s[:-1]
        else:
            return s, u''.join(ending)

    return u'', ''.join(ending)


def translate_string(s):
    # If it consists solely of whitespace, skip it.
    if is_whitespace(s):
        return s

    hamm = HtmlAwareMessageMunger()
    hamm.feed(s)
    out = hamm.result()

    # Add color which causes every string to be longer.
    s, ending = split_ending(out)
    out = s + u' ' + COLOR[len(out) % len(COLOR)] + ending

    # This guarantees that every string has at least one
    # unicode charater
    if '!' not in out:
        out = out + u'!'

    # Replace all ! with related unicode character.
    out = out.replace(u'!', u'\u2757')
    return out


def translate_file(fname):
    po = polib.pofile(fname)
    po.metadata['Language'] = 'Pirate'
    po.metadata['Plural-Forms'] = 'nplurals=2; plural= n != 1'
    po.metadata['Content-Type'] = 'text/plain; charset=UTF-8'
    count = 0
    for entry in po:
        if entry.msgid_plural:
            entry.msgstr_plural['0'] = translate_string(entry.msgid)
            entry.msgstr_plural['1'] = translate_string(entry.msgid_plural)
        else:
            entry.msgstr = translate_string(entry.msgid)

        if 'fuzzy' in entry.flags:
            entry.flags.remove('fuzzy')  # clear the fuzzy flag
        count += 1
    print 'Munged %d messages in %s' % (count, fname)
    po.save()
