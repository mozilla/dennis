import os

import polib

from dennis.tools import VariableTokenizer, Terminal


# blessings.Terminal and our mock Terminal don't maintain any state
# so we can just make it global
TERMINAL = Terminal()


class Linter(object):
    def __init__(self, var_types):
        self.vartok = VariableTokenizer(var_types)

    def compare_tokens(self, id_tokens, str_tokens):
        """Compares str_tokens to id_tokens

        This returns two lists:

        * list of missing tokens: any tokens in id_tokens that aren't
          also in str_tokens

        * list of invalid tokens: any tokens in str_tokens that aren't
          also in id_tokens --- these are the ones that cause errors
          when interpolating


        :arg id_tokens: list of tokens from the source text
        :arg str_tokens: list of tokens from the translated text

        :returns: tuple of (list of missing tokens, list of invalid tokens)

        """
        if str_tokens is None:
            # If str_tokens is None, they haven't translated the
            # msgid, so there's no entry. I'm pretty sure this only
            # applies to plurals.
            return [], []

        invalid_tokens = []
        missing_tokens = []

        for token in id_tokens:
            if token not in str_tokens:
                missing_tokens.append(token)

        for token in str_tokens:
            if token not in id_tokens:
                invalid_tokens.append(token)

        return missing_tokens, invalid_tokens

    def format_with_errors(self, text, req_tokens):
        output = []
        for token in self.vartok.tokenize(text):
            if self.vartok.is_token(token) and token not in req_tokens:
                output.append(TERMINAL.bold_red(token))
            else:
                output.append(token)
        return u''.join(output)

    def verify(self, msgid, id_text, id_tokens, str_text, str_tokens, index):
        """Verifies strings, prints messages to console

        :returns: True if there were errors, False otherwise

        """
        # If the str_text is empty, there's no translation which we
        # consider "fine".
        if not str_text.strip():
            return True

        missing, invalid = self.compare_tokens(id_tokens, str_tokens)

        if not missing and not invalid:
            return True

        print ''

        if missing:
            print u'{label}: {tokens}'.format(
                label=TERMINAL.bold_yellow('Warning: missing tokens'),
                tokens=u', '.join(missing))

        if invalid:
            print u'{label}: {tokens}'.format(
                label=TERMINAL.bold_red('Error: invalid tokens'),
                tokens=', '.join(invalid))

        name = TERMINAL.yellow('msgid')
        print '{0}: "{1}"'.format(name, msgid)

        if index is not None:
            # Print the plural
            name = TERMINAL.yellow('msgid_plural')
            print '{0}: "{1}"'.format(name, id_text)

        # Print the translated string with token errors
        if index is not None:
            name = 'msgstr[{index}]'.format(index=index)
        else:
            name = 'msgstr'
        print u'{0}: "{1}"'.format(
            TERMINAL.yellow(name),
            self.format_with_errors(str_text, id_tokens))

        if invalid:
            return False

        return True

    def verify_file(self, fname):
        """Verifies file fname

        This prints to stdout errors it found in fname. It returns the
        number of errors.

        """
        if not fname.endswith('.po'):
            print '{fname} is not a .po file.'.format(fname=fname)
            return 1

        print 'Working on {fname}'.format(fname=os.path.abspath(fname))

        po = polib.pofile(fname)

        count = 0
        bad_count = 0

        for entry in po:
            if not entry.msgid_plural:
                if not entry.msgid and entry.msgstr:
                    continue
                id_tokens = self.vartok.extract_tokens(entry.msgid)
                str_tokens = self.vartok.extract_tokens(entry.msgstr)

                if not self.verify(entry.msgid, entry.msgid, id_tokens,
                                   entry.msgstr, str_tokens, None):
                    bad_count += 1

            else:
                for key in sorted(entry.msgstr_plural.keys()):
                    if key == '0':
                        # This is the 1 case.
                        text = entry.msgid
                    else:
                        text = entry.msgid_plural
                    id_tokens = self.vartok.extract_tokens(text)

                    str_tokens = self.vartok.extract_tokens(
                        entry.msgstr_plural[key])
                    if not self.verify(entry.msgid, text, id_tokens,
                                       entry.msgstr_plural[key], str_tokens,
                                       key):
                        bad_count += 1

            count += 1

        print (
            '\nVerified {count} messages in {fname}. '
            '{badcount} errors.'.format(
                count=count, fname=fname, badcount=bad_count))

        return bad_count

    def verify_directory(self, dir_):
        """Verifies all the .po files in directory tree dir_"""
        po_files = {}
        for root, dirs, files in os.walk(dir_):
            for fn in files:
                if not fn.endswith('.po'):
                    continue

                fn = os.path.join(root, fn)

                po_files[fn] = self.verify_file(fn)
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
