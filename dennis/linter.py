import polib

from dennis.tools import VariableTokenizer


def _compare_lists(list_a, list_b):
    """Compares contents of two lists

    This returns two lists:

    * list of tokens in list_a missing from list_b

    * list of tokens in list_b missing from list_a

    :returns: tuple of (list of tokens in list_a not in list_b, list
        of tokens in list_b not in list_a)

    """
    return (
        [token for token in list_a if token not in list_b],
        [token for token in list_b if token not in list_a]
    )


class LintItem(object):
    """Holds all the data involved in a lint item"""
    def __init__(self, poentry, msgid, msgid_text, msgid_tokens,
                 msgstr_text, msgstr_tokens, index):
        self.poentry = poentry

        self.msgid = msgid
        self.msgid_text = msgid_text
        self.msgid_tokens = msgid_tokens
        self.msgstr_text = msgstr_text
        self.msgstr_tokens = msgstr_tokens
        self.index = index

        # If the str_text is empty, there's no translation which we
        # consider "fine".
        if not msgstr_text.strip():
            self.missing, self.invalid = [], []
        else:
            self.missing, self.invalid = _compare_lists(
                msgid_tokens, msgstr_tokens)


class Linter(object):
    def __init__(self, var_types):
        # FIXME - this is a horrible name
        self.vartok = VariableTokenizer(var_types)

    def verify_file(self, filename_or_string):
        """Verifies strings in file.

        :arg filename_or_string: filename to verify or the contents of
            a pofile as a string

        :returns: for each string in the pofile, this returns a None
            if there were no issues or a LintError if there were
            issues

        :raises IOError: if the file is not a valid .po file or
            doesn't exist
        """
        po = polib.pofile(filename_or_string)

        results = []

        for entry in po:
            if not entry.msgid_plural:
                if not entry.msgid and entry.msgstr:
                    continue
                id_tokens = self.vartok.extract_tokens(entry.msgid)
                str_tokens = self.vartok.extract_tokens(entry.msgstr)

                results.append(
                    LintItem(entry, entry.msgid, entry.msgid,
                             id_tokens, entry.msgstr,
                             str_tokens, None))

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
                    results.append(
                        LintItem(entry, entry.msgid, text, id_tokens,
                                 entry.msgstr_plural[key],
                                 str_tokens, key))

        return results


def format_with_errors(terminal, vartok, text, available_tokens):
    """Turns invalid tokens in the text red for output

    :arg terminal: a blessings Terminal or mock Terminal
    :arg vartok: the variable tokenizer to use
    :arg text: the text holding the tokens
    :arg available_tokens: valid tokens that should be in the
        text---anything else is an invalid token and will be turned
        bold red.

    :returns: the text with invalid tokens bold red

    """
    output = []
    for token in vartok.tokenize(text):
        if vartok.is_token(token) and token not in available_tokens:
            output.append(terminal.bold_red(token))
        else:
            output.append(token)
    return u''.join(output)
