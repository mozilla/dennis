import polib

from dennis.tools import VariableTokenizer


class LintError(object):
    """Holds all the data involved in a lint error"""
    def __init__(self, msgid, id_text, id_tokens, str_text, str_tokens,
                 index, missing, invalid):
        self.msgid = msgid
        self.id_text = id_text
        self.id_tokens = id_tokens
        self.str_text = str_text
        self.str_tokens = str_tokens
        self.index = index

        self.missing_tokens = missing
        self.invalid_tokens = invalid


def compare_lists(list_a, list_b):
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


class Linter(object):
    def __init__(self, var_types):
        # FIXME - this is a horrible name
        self.vartok = VariableTokenizer(var_types)

    def verify(self, msgid, id_text, id_tokens, str_text, str_tokens,
               index):
        """Verifies strings, prints messages to console

        Lots of arguments.

        :returns: None if it was fine or a LintError if there were
            problems

        """
        # If the str_text is empty, there's no translation which we
        # consider "fine".
        if not str_text.strip():
            return None

        if not str_tokens:
            # If str_tokens is None, they haven't translated the
            # msgid, so there's no entry. I'm pretty sure this only
            # applies to plurals.
            missing, invalid = [], []
        else:
            missing, invalid = compare_lists(id_tokens, str_tokens)

        if not missing and not invalid:
            return None

        return LintError(msgid, id_text, id_tokens, str_text, str_tokens,
                         index, missing, invalid)

    def verify_file(self, fname):
        """Verifies strings in file.

        :arg fname: filename to verify

        :returns: list of LintError objects

        """
        po = polib.pofile(fname)

        errors = []

        for entry in po:
            if not entry.msgid_plural:
                if not entry.msgid and entry.msgstr:
                    continue
                id_tokens = self.vartok.extract_tokens(entry.msgid)
                str_tokens = self.vartok.extract_tokens(entry.msgstr)

                errors.append(self.verify(entry.msgid, entry.msgid,
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
                    errors.append(self.verify(entry.msgid, text, id_tokens,
                                              entry.msgstr_plural[key],
                                              str_tokens, key))

        return errors


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
