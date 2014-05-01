import re
from collections import namedtuple

import polib

from dennis.tools import VariableTokenizer, parse_dennis_note


TranslatedString = namedtuple(
    'TranslatedString',
    ('msgid_fields', 'msgid_strings', 'msgstr_field', 'msgstr_string'))


class LintedEntry(object):
    def __init__(self, poentry):
        self.poentry = poentry
        self.msgid = poentry.msgid

        strs = []

        if not poentry.msgid_plural:
            strs.append(
                TranslatedString(
                    ['msgid'], [poentry.msgid], 'msgstr', poentry.msgstr))

        else:
            msgid_fields = ('msgid', 'msgid_plural')
            msgid_strings = (poentry.msgid, poentry.msgid_plural)

            for key in sorted(poentry.msgstr_plural.keys()):
                strs.append(
                    TranslatedString(
                        msgid_fields,
                        msgid_strings,
                        'msgstr[{0}]'.format(key),
                        poentry.msgstr_plural[key]))

        # List of (msgid fields, msgid strings, msgstr field, msgstr
        # string) namedtuples
        self.strs = strs

        self.warnings = []
        self.errors = []

    def add_warning(self, code, trstr, msg):
        self.warnings.append((code, trstr, msg))

    def add_error(self, code, trstr, msg):
        self.errors.append((code, trstr, msg))

    def has_problems(self, errorsonly=False):
        if errorsonly:
            return bool(self.errors)
        return bool(self.warnings or self.errors)


class LintRule(object):
    num = ''
    name = ''
    desc = ''

    def lint(self, vartok, linted_entry):
        """Takes a linted entry and adds errors and warnings

        :arg vartok: the variable tokenizer to use for tokenizing
            on variable tokens
        :arg linted_entry: the LintedEntry to work on

        """
        raise NotImplemented


class MalformedNoTypeLintRule(LintRule):
    num = 'E101'
    name = 'notype'
    desc = '%(count) with no type at the end'

    def lint(self, vartok, linted_entry):
        # This only applies if one of the variable tokenizers
        # is PythonPercentVar.
        if not vartok.contains('pysprintf'):
            return

        malformed_re = re.compile(r'(?:%[\(][^\)\s]+[\)](?:\s|$))')

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            malformed = malformed_re.findall(trstr.msgstr_string)
            if not malformed:
                continue

            malformed = [item.strip() for item in malformed]
            linted_entry.add_error(
                self.num,
                trstr,
                u'type missing: {0}'.format(u', '.join(malformed)))


class MalformedMissingRightBraceLintRule(LintRule):
    num = 'E102'
    name = 'missingrightbrace'
    desc = '{foo with missing }'

    def lint(self, vartok, linted_entry):
        # This only applies if one of the variable tokenizers
        # is PythonFormatVar.
        if not vartok.contains('pyformat'):
            return

        malformed_re = re.compile(r'(?:\{[^\}]+(?:\{|$))')

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            malformed = malformed_re.findall(trstr.msgstr_string)
            if not malformed:
                continue

            malformed = [item.strip() for item in malformed]
            linted_entry.add_error(
                self.num,
                trstr,
                u'missing right curly-brace: {0}'.format(
                    u', '.join(malformed)))


class MalformedMissingLeftBraceLintRule(LintRule):
    num = 'E103'
    name = 'missingleftbrace'
    desc = 'foo} with missing {'

    def lint(self, vartok, linted_entry):
        # This only applies if one of the variable tokenizers
        # is PythonFormatVar.
        if not vartok.contains('pyformat'):
            return

        malformed_re = re.compile(r'(?:(?:^|\})[^\{]+\})')

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            malformed = malformed_re.findall(trstr.msgstr_string)
            if not malformed:
                continue

            malformed = [item.strip() for item in malformed]
            linted_entry.add_error(
                self.num,
                trstr,
                u'missing left curly-brace: {0}'.format(
                    u', '.join(malformed)))


class MissingVarsLintRule(LintRule):
    num = 'W202'
    name = 'missingvars'
    desc = 'Checks for variables in msgid, but missing in msgstr'

    def lint(self, vartok, linted_entry):
        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            msgid_tokens = vartok.extract_tokens(' '.join(trstr.msgid_strings))
            msgstr_tokens = vartok.extract_tokens(trstr.msgstr_string)

            missing = msgid_tokens.difference(msgstr_tokens)

            if missing:
                linted_entry.add_warning(
                    self.num,
                    trstr,
                    u'missing variables: {0}'.format(
                        u', '.join(sorted(missing))))


class InvalidVarsLintRule(LintRule):
    num = 'E201'
    name = 'invalidvars'
    desc = 'Checks for variables not in msgid, but in msgstr'

    def lint(self, vartok, linted_entry):
        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            msgid_tokens = vartok.extract_tokens(' '.join(trstr.msgid_strings))
            msgstr_tokens = vartok.extract_tokens(trstr.msgstr_string)

            invalid = msgstr_tokens.difference(msgid_tokens)

            if invalid:
                linted_entry.add_error(
                    self.num,
                    trstr,
                    u'invalid variables: {0}'.format(
                        u', '.join(sorted(invalid))))


def get_available_lint_rules(name_and_num=False):
    lint_rules = {}

    for name, thing in globals().items():
        try:
            if issubclass(thing, LintRule) and thing.num:
                lint_rules[thing.num] = thing
                if name_and_num:
                    lint_rules[thing.name] = thing
        except TypeError:
            pass

    return lint_rules


class InvalidRulesSpec(Exception):
    pass


def convert_rules(rules_spec):
    # This removes empty strings from the rules_spec.
    rules_spec = [rule for rule in rules_spec if rule]

    if not rules_spec:
        lint_rules = get_available_lint_rules()
        return [rule() for num, rule in lint_rules.items()]

    try:
        lint_rules = get_available_lint_rules(name_and_num=True)
        rules = [lint_rules[rule]() for rule in rules_spec]
    except KeyError:
        raise InvalidRulesSpec(rules_spec)

    return rules


class Linter(object):
    def __init__(self, vars_, rules_spec):
        self.vartok = VariableTokenizer(vars_)
        self.rules_spec = rules_spec
        self.rules = convert_rules(self.rules_spec)

    def lint_poentry(self, poentry):
        linted_entry = LintedEntry(poentry)

        skip = parse_dennis_note(poentry.comment)

        # Check the comment to see if what we should ignore.
        for lint_rule in self.rules:
            if skip == '*' or lint_rule.num in skip:
                continue

            lint_rule.lint(self.vartok, linted_entry)

        return linted_entry

    def verify_file(self, filename_or_string):
        """Verifies strings in file.

        :arg filename_or_string: filename to verify or the contents of
            a pofile as a string

        :returns: list of LintedEntry objects each with errors and
            warnings

        :raises IOError: if the file is not a valid .po file or
            doesn't exist
        """
        po = polib.pofile(filename_or_string)
        return [
            self.lint_poentry(entry) for entry in po.translated_entries()
        ]
