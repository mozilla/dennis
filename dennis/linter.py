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


class Linter(object):
    def __init__(self, var_types):
        # FIXME - this is a horrible name
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

        missing, invalid = self.compare_tokens(id_tokens, str_tokens)

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
