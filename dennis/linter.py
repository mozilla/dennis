import re
import uuid
from collections import namedtuple
from itertools import zip_longest

from dennis.tools import (
    VariableTokenizer,
    all_subclasses,
    parse_dennis_note,
    parse_pofile,
)


IdString = namedtuple("IdString", ("msgid_fields", "msgid_strings"))
TranslatedString = namedtuple(
    "TranslatedString",
    ("msgid_fields", "msgid_strings", "msgstr_field", "msgstr_string"),
)


WARNING = "warn"
ERROR = "err"


class HTMLParseError(Exception):
    pass


class LintMessage:
    def __init__(self, kind, line, col, code, msg, poentry):
        self.kind = kind
        self.line = line
        self.col = col
        self.code = code
        self.msg = msg
        self.poentry = poentry

    def __repr__(self):
        return "<LintedMessage {} {}:{} {} {}>".format(
            self.kind, self.line, self.col, self.code, self.msg
        )


class LintedEntry:
    def __init__(self, poentry):
        self.poentry = poentry
        self.msgid = poentry.msgid

    @property
    def str(self):
        poentry = self.poentry
        if poentry.msgid_plural:
            msgid_fields = ("msgid", "msgid_plural")
            msgid_strings = (poentry.msgid, poentry.msgid_plural)
        else:
            msgid_fields = ("msgid",)
            msgid_strings = (poentry.msgid,)

        return IdString(msgid_fields, msgid_strings)

    @property
    def strs(self):
        poentry = self.poentry
        strs = []

        if not poentry.msgid_plural:
            strs.append(
                TranslatedString(["msgid"], [poentry.msgid], "msgstr", poentry.msgstr)
            )

        else:
            msgid_fields = ("msgid", "msgid_plural")
            msgid_strings = (poentry.msgid, poentry.msgid_plural)

            for key in sorted(poentry.msgstr_plural.keys()):
                strs.append(
                    TranslatedString(
                        msgid_fields,
                        msgid_strings,
                        "msgstr[{}]".format(key),
                        poentry.msgstr_plural[key],
                    )
                )

        # List of TranslatedStrings
        return strs


class LintRule:
    num = ""
    name = ""
    desc = ""

    def lint(self, vartok, linted_entry):
        """Takes a linted entry and generates LintMessages

        :arg vartok: the variable tokenizer for extracting variables
        :arg linted_entry: the LintedEntry to work on

        :returns: list of LintMeessages or empty list

        """
        raise NotImplementedError


class MalformedNoTypeLintRule(LintRule):
    num = "E101"
    name = "notype"
    desc = "%(count) with no type at the end"

    def lint(self, vartok, linted_entry):
        msgs = []

        # This only applies if one of the variable tokenizers is python-format.
        if not vartok.contains("python-format"):
            return msgs

        malformed_re = re.compile(
            r"(?:"
            r"%"  # %
            r"[\(][^\)\s]+[\)]"  # things in parens or not
            r"(?:(?=[^diouxefGgcrs])|$)"  # end of string or something that's not a format char
            r")"
        )

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            malformed = malformed_re.findall(trstr.msgstr_string)
            if not malformed:
                continue

            malformed = [item.strip() for item in malformed]
            msgs.append(
                LintMessage(
                    ERROR,
                    linted_entry.poentry.linenum,
                    0,
                    self.num,
                    "type missing: {}".format(", ".join(malformed)),
                    linted_entry.poentry,
                )
            )

        return msgs


class MalformedMissingRightBraceLintRule(LintRule):
    num = "E102"
    name = "missingrightbrace"
    desc = "{foo with missing }"

    def lint(self, vartok, linted_entry):
        msgs = []

        # This only applies if one of the variable tokenizers is python-brace-format.
        if not vartok.contains("python-brace-format"):
            return []

        malformed_re = re.compile(r"(?:\{[^\}]+(?:\{|$))")
        double_open = str(uuid.uuid4())
        double_close = str(uuid.uuid4())

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            malformed = malformed_re.findall(
                trstr.msgstr_string.replace("{{", double_open).replace(
                    "}}", double_close
                )
            )
            if not malformed:
                continue

            malformed = [
                item.strip().replace(double_open, "{{").replace(double_close, "}}")
                for item in malformed
            ]
            msgs.append(
                LintMessage(
                    ERROR,
                    linted_entry.poentry.linenum,
                    0,
                    self.num,
                    "missing right curly-brace: {}".format(", ".join(malformed)),
                    linted_entry.poentry,
                )
            )

        return msgs


class MalformedMissingLeftBraceLintRule(LintRule):
    num = "E103"
    name = "missingleftbrace"
    desc = "foo} with missing {"

    def lint(self, vartok, linted_entry):
        msgs = []

        # This only applies if one of the variable tokenizers is python-brace-format.
        if not vartok.contains("python-brace-format"):
            return []

        malformed_re = re.compile(r"(?:(?:^|\})[^\{]*\})")
        double_open = str(uuid.uuid4())
        double_close = str(uuid.uuid4())

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            malformed = malformed_re.findall(
                trstr.msgstr_string.replace("{{", double_open).replace(
                    "}}", double_close
                )
            )
            if not malformed:
                continue

            malformed = [
                item.strip().replace(double_open, "{{").replace(double_close, "}}")
                for item in malformed
            ]
            msgs.append(
                LintMessage(
                    ERROR,
                    linted_entry.poentry.linenum,
                    0,
                    self.num,
                    "missing left curly-brace: {}".format(", ".join(malformed)),
                    linted_entry.poentry,
                )
            )
        return msgs


class BadFormatLintRule(LintRule):
    num = "E104"
    name = "badformat"
    desc = "% followed by a bad format character"

    def lint(self, vartok, linted_entry):
        msgs = []

        # This only applies if one of the variable tokenizers is python-format.
        if not vartok.contains("python-format"):
            return []

        splitter = re.compile(r"(\%(?:.|$))")

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            msgid_tokens = list(vartok.extract_tokens(" ".join(trstr.msgid_strings)))
            if not msgid_tokens:
                continue
            # FIXME: Pretty sure we can just check the first token because they'll
            # all have to be the same kind of thing.
            first_token = msgid_tokens[0]
            if not (len(first_token) == 2 and first_token[0] == "%"):
                continue

            for match in splitter.findall(trstr.msgstr_string):
                if len(match) == 1 or match[1] not in "(diouxefGgcrs%":
                    msgs.append(
                        LintMessage(
                            ERROR,
                            linted_entry.poentry.linenum,
                            0,
                            self.num,
                            "bad format character: {}".format(match),
                            linted_entry.poentry,
                        )
                    )
        return msgs


class MissingVarsLintRule(LintRule):
    num = "W202"
    num_error = "E202"
    name = "missingvars"
    desc = "Checks for variables in msgid, but missing in msgstr"

    def lint(self, vartok, linted_entry):
        msgs = []

        # If there are no variable formats, skip this rule.
        if not vartok.formats:
            return []

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            if len(trstr.msgid_strings) > 1:
                # If the msgstr uses a variable that isn't in any of
                # the msgid strings, then that's an error (and handled
                # by a different LintRule). Anything else we should
                # ignore.
                continue

            msgid_tokens = vartok.extract_tokens(" ".join(trstr.msgid_strings))
            msgstr_tokens = vartok.extract_tokens(trstr.msgstr_string)

            missing = msgid_tokens.difference(msgstr_tokens)

            if missing:
                if vartok.contains("python-format") and len(
                    [var for var in missing if len(var) == 2 and var[0] == "%"]
                ):
                    # If we're looking at python-format variables and one of these is a
                    # python-format variable like %s, then this is an error--not a warning.
                    msgs.append(
                        LintMessage(
                            ERROR,
                            linted_entry.poentry.linenum,
                            0,
                            self.num_error,
                            "missing variables: {}".format(", ".join(sorted(missing))),
                            linted_entry.poentry,
                        )
                    )
                else:
                    # If this is not python-format variables, then this is just a warning.
                    msgs.append(
                        LintMessage(
                            WARNING,
                            linted_entry.poentry.linenum,
                            0,
                            self.num,
                            "missing variables: {}".format(", ".join(sorted(missing))),
                            linted_entry.poentry,
                        )
                    )
        return msgs


class BlankLintRule(LintRule):
    num = "W301"
    name = "blank"
    desc = "Translated string is only whitespace"

    def lint(self, vartok, linted_entry):
        msgs = []

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            if trstr.msgstr_string.isspace():
                msgs.append(
                    LintMessage(
                        WARNING,
                        linted_entry.poentry.linenum,
                        0,
                        self.num,
                        "translated string is solely whitespace",
                        linted_entry.poentry,
                    )
                )

        return msgs


class UnchangedLintRule(LintRule):
    num = "W302"
    name = "unchanged"
    desc = "Makes sure string is actually translated"

    def lint(self, vartok, linted_entry):
        msgs = []

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            if trstr.msgstr_string in trstr.msgid_strings:
                msgs.append(
                    LintMessage(
                        WARNING,
                        linted_entry.poentry.linenum,
                        0,
                        self.num,
                        "translated string is same as source string",
                        linted_entry.poentry,
                    )
                )

        return msgs


class MismatchedHTMLLintRule(LintRule):
    num = "W303"
    num_error = "W304"
    name = "html"
    desc = "Checks for matching html between source and translated strings"

    def lint(self, vartok, linted_entry):
        msgs = []

        from dennis.translator import HTMLExtractorTransform, Token

        html = HTMLExtractorTransform()

        def equiv(left, right):
            return left == right

        def tokenize(text):
            """Tokenizes the text using the HTMLExtractorTransform

            :raises HTMLParseError: If it's invalid HTML.

            """
            tokens = [
                token
                for token in html.transform(vartok, [Token(text)])
                if token.type == "html" and not token.s.startswith("&")
            ]
            return sorted(tokens, key=lambda token: token.s)

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            try:
                msgid_parts = tokenize(trstr.msgid_strings[0])
            except HTMLParseError as exc:
                errmsg = "invalid html: msgid has invalid html {}".format(exc)
                msgs.append(
                    LintMessage(
                        WARNING,
                        linted_entry.poentry.linenum,
                        0,
                        self.num_error,
                        errmsg,
                        linted_entry.poentry,
                    )
                )
                return msgs

            if len(trstr.msgid_strings) > 1:
                # If this is a plural, then we check to see if the two
                # msgid strings match each other. If not, then we move
                # on because I have no idea what to do in this case.
                try:
                    msgid_plural_parts = tokenize(trstr.msgid_strings[1])
                except HTMLParseError as exc:
                    errmsg = "invalid html: msgid_plural has invalid html {}".format(
                        exc
                    )

                    msgs.append(
                        LintMessage(
                            WARNING,
                            linted_entry.poentry.linenum,
                            0,
                            self.num_error,
                            errmsg,
                            linted_entry.poentry,
                        )
                    )
                    return msgs

                zipped_parts = zip_longest(
                    msgid_parts, msgid_plural_parts, fillvalue=None
                )

                for left, right in zipped_parts:
                    if not left or not right or not equiv(left, right):
                        return []

            try:
                msgstr_parts = tokenize(trstr.msgstr_string)
            except HTMLParseError as exc:
                errmsg = "invalid html: msgstr has invalid html {}".format(exc)
                msgs.append(
                    LintMessage(
                        WARNING,
                        linted_entry.poentry.linenum,
                        0,
                        self.num_error,
                        errmsg,
                        linted_entry.poentry,
                    )
                )
                return msgs

            for left, right in zip_longest(msgid_parts, msgstr_parts, fillvalue=None):
                if not left or not right or not equiv(left, right):
                    msgs.append(
                        LintMessage(
                            WARNING,
                            linted_entry.poentry.linenum,
                            0,
                            self.num,
                            'different html: "{}" vs. "{}"'.format(
                                left.s if left else "", right.s if right else ""
                            ),
                            linted_entry.poentry,
                        )
                    )
                    break
        return msgs


class EmptyLintRule(LintRule):
    num = "W304"
    name = "empty"
    desc = "Untranslated string"

    def lint(self, vartok, linted_entry):
        msgs = []

        for trstr in linted_entry.strs:
            if trstr.msgstr_string:
                continue

            msgs.append(
                LintMessage(
                    WARNING,
                    linted_entry.poentry.linenum,
                    0,
                    self.num,
                    "String is untranslated",
                    linted_entry.poentry,
                )
            )

        return msgs


class InvalidVarsLintRule(LintRule):
    num = "E201"
    name = "invalidvars"
    desc = "Checks for variables not in msgid, but in msgstr"

    def lint(self, vartok, linted_entry):
        # If there are no variable formats, skip this rule.
        if not vartok.formats:
            return []

        msgs = []
        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            msgid_tokens = vartok.extract_tokens(" ".join(trstr.msgid_strings))
            # If this is python-format or python-brace-format and there are
            # no tokens in the msgid, then "no tokens, no problem".
            if not msgid_tokens:
                continue

            msgstr_tokens = vartok.extract_tokens(trstr.msgstr_string)

            invalid = msgstr_tokens.difference(msgid_tokens)

            if invalid:
                msgs.append(
                    LintMessage(
                        ERROR,
                        linted_entry.poentry.linenum,
                        0,
                        self.num,
                        "invalid variables: {}".format(", ".join(sorted(invalid))),
                        linted_entry.poentry,
                    )
                )
        return msgs


def get_lint_rules(with_names=False):
    lint_rules = {}

    for cls in all_subclasses(LintRule):
        if cls.num:
            lint_rules[cls.num] = cls
            if with_names and cls.name:
                lint_rules[cls.name] = cls

    return lint_rules


def convert_rules(rules_spec):
    lint_rules = get_lint_rules(with_names=True)
    rules = [lint_rules[rule]() for rule in rules_spec if rule in lint_rules]
    return rules


class Linter:
    def __init__(self, vars_, rules_spec):
        self.vartok = VariableTokenizer(vars_)
        self.rules_spec = rules_spec
        self.rules = convert_rules(self.rules_spec)

    def lint_poentry(self, poentry):
        linted_entry = LintedEntry(poentry)

        skip = parse_dennis_note(poentry.comment)

        msgs = []

        # Check the comment to see if what we should ignore.
        for lint_rule in self.rules:
            if skip == "*" or lint_rule.num in skip:
                continue

            msgs.extend(lint_rule.lint(self.vartok, linted_entry))

        return msgs

    def verify_file(self, filename_or_string):
        """Verifies strings in file.

        :arg filename_or_string: filename to verify or the contents of
            a pofile as a string

        :returns: list of LintMessage objects

        :raises IOError: if the file is not a valid .po file or
            doesn't exist
        """
        po = parse_pofile(filename_or_string)
        msgs = []
        for entry in po:
            if entry.fuzzy or entry.obsolete:
                continue
            msgs.extend(self.lint_poentry(entry))

        return msgs
