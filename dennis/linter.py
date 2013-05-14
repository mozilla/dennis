import itertools
import os

import polib

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

from dennis.tools import extract_tokens, is_token, tokenize


# blessings.Terminal and our mock Terminal don't maintain any state
# so we can just make it global
TERMINAL = Terminal()


FINE = 0            # translated and source text have same tokens
NOT_TRANSLATED = 1  # text hasn't been translated
MISSING_TOKENS = 2  # translated text is missing tokens from source
WRONG_TOKENS = 3    # translated text has tokens not in source

def compare_tokens(id_tokens, str_tokens):
    if str_tokens is None:
        # If str_tokens is None, they haven't translated the msgid, so
        # there's no entry. I'm pretty sure this only applies to
        # plurals.
        return NOT_TRANSLATED

    for id_token, str_token in itertools.izip_longest(
        id_tokens, str_tokens, fillvalue=None):
       
        if id_token is None:
            return WRONG_TOKENS
        if str_token is None:
            return MISSING_TOKENS
        if id_token != str_token:
            return WRONG_TOKENS
    return FINE


def format_with_errors(text, req_tokens):
    output = []
    for token in tokenize(text):
        if is_token(token) and token not in req_tokens:
            output.append(TERMINAL.bold_red(token))
        else:
            output.append(token)
    return u''.join(output)


def verify(msgid, id_text, id_tokens, str_text, str_tokens, index):
    # If the str_text is empty, there's no translation which we consider
    # "fine".
    if not str_text.strip():
        return True

    ret = compare_tokens(id_tokens, str_tokens)

    # If the text isn't translated, we consider that "fine".
    if ret == NOT_TRANSLATED:
        return True

    if ret == FINE:
        return True

    print ''

    if ret == WRONG_TOKENS:
        label = TERMINAL.bold_red('Invalid tokens')
    elif ret == MISSING_TOKENS:
        label = TERMINAL.bold_yellow('Missing tokens')

    print u'{label}: {id_tokens} VS. {str_tokens}'.format(
        label=label,
        id_tokens=u', '.join(id_tokens),
        str_tokens=u', '.join(str_tokens))

    name = 'msgid'
    if len(msgid) <= 50:
        print '{0}: "{1}"'.format(name, msgid)
    else:
        print '{0}:'.format(name)
        print msgid

    if index is not None:
        # Print the plural
        if len(id_text) <= 50:
            print '{0}: "{1}"'.format(name, id_text)
        else:
            print '{0}:'.format(name)
            print id_text

    # Print the translated string with token errors
    if index is not None:
        name = 'msgstr[{index}]'.format(index=index)
    else:
        name = 'msgstr'
    if len(str_text) <= 50:
        print u'{0}: "{1}"'.format(
            name, format_with_errors(str_text, id_tokens))
    else:
        print u'{0}:'.format(name)
        print format_with_errors(str_text, id_tokens)

    return False


def verify_file(fname):
    """Verifies file fname

    This prints to stdout errors it found in fname. It returns the
    number of errors.

    """
    if not fname.endswith('.po'):
        print '{fname} is not a .po file.'.format(fname=fname)
        return 1

    print 'Working on {fname}'.format(fname=fname)

    po = polib.pofile(fname)

    count = 0
    bad_count = 0

    for entry in po:
        if not entry.msgid_plural:
            if not entry.msgid and entry.msgstr:
                continue
            id_tokens = extract_tokens(entry.msgid)
            str_tokens = extract_tokens(entry.msgstr)

            if not verify(entry.msgid, entry.msgid, id_tokens, entry.msgstr,
                    str_tokens, None):
                bad_count += 1

        else:
            for key in sorted(entry.msgstr_plural.keys()):
                if key == '0':
                    # This is the 1 case.
                    text = entry.msgid
                else:
                    text = entry.msgid_plural
                id_tokens = extract_tokens(text)

                str_tokens = extract_tokens(entry.msgstr_plural[key])
                if not verify(entry.msgid, text, id_tokens,
                              entry.msgstr_plural[key], str_tokens, key):
                    bad_count += 1

        count += 1

    print ('\nVerified {count} messages in {fname}. '
           '{badcount} possible errors.'.format(
            count=count, fname=fname, badcount=bad_count))

    return bad_count


def verify_directory(dir_):
    po_files = {}
    for root, dirs, files in os.walk(dir_):
        for fn in files:
            if not fn.endswith('.po'):
                continue

            fn = os.path.join(root, fn)

            po_files[fn] = verify_file(fn)
            print '---'

    total_errors = sum(val for key, val in po_files.items())
    if total_errors == 0:
        return 0

    print 'Problem locale files:'
    po_files = sorted([(val, key) for key, val in po_files.items()],
                      reverse=True)
    for val, key in po_files:
        if val:
            print '{val:>5} {key}'.format(key=key, val=val)

    return 1
