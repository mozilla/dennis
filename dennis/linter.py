from collections import namedtuple

import polib

from dennis.tools import VariableTokenizer


TranslatedString = namedtuple(
    'TranslatedString',
    ('msgid_field', 'msgid_string', 'msgstr_field', 'msgstr_string'))


class LintedEntry(object):
    def __init__(self, poentry):
        self.poentry = poentry
        self.msgid = poentry.msgid

        strs = []

        if not poentry.msgid_plural:
            strs.append(
                TranslatedString(
                    'msgid', poentry.msgid, 'msgstr', poentry.msgstr))

        else:
            for key in sorted(poentry.msgstr_plural.keys()):
                if key == '0':
                    # This is the 1 case
                    msgid_field = 'msgid'
                    text = poentry.msgid
                else:
                    msgid_field = 'msgid_plural'
                    text = poentry.msgid_plural
                strs.append(
                    TranslatedString(
                        msgid_field,
                        text,
                        'msgstr[{0}]'.format(key),
                        poentry.msgstr_plural[key]))

        # List of (msgid field, msgid string, msgstr field, msgstr
        # string) tuples
        self.strs = strs

        self.warnings = []
        self.errors = []

    def add_warning(self, code, trstr, msg):
        self.warnings.append((code, trstr, msg))

    def add_error(self, code, trstr, msg):
        self.errors.append((code, trstr, msg))

    def has_problems(self):
        return bool(self.warnings or self.errors)


class LintRule(object):
    name = ''
    desc = ''

    def lint(self, vartok, linted_entry):
        """Takes a linted entry and adds errors and warnings

        :arg vartok: the variable tokenizer to use for tokenizing
            on variable tokens
        :arg linted_entry: the LintedEntry to work on

        """
        raise NotImplemented


class MismatchedVarsLintRule(LintRule):
    name = 'mismatched'
    desc = 'Checks for variables in one string not in the other'

    @classmethod
    def compare_lists(cls, list_a, list_b):
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

    def lint(self, vartok, linted_entry):
        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            missing, invalid = self.compare_lists(
                vartok.extract_tokens(trstr.msgid_string),
                vartok.extract_tokens(trstr.msgstr_string))

            if missing:
                linted_entry.add_warning(
                    self.name,
                    trstr,
                    u'missing variables: {0}'.format(u', '.join(missing)))

            if invalid:
                linted_entry.add_error(
                    self.name,
                    trstr,
                    u'invalid variables: {0}'.format(u', '.join(invalid)))


def get_available_lint_rules():
    lint_rules = {}

    for name, thing in globals().items():
        if (name.endswith('LintRule')
            and issubclass(thing, LintRule)
            and thing.name):
            lint_rules[thing.name] = thing

    return lint_rules


class InvalidRulesSpec(Exception):
    pass


def convert_rules(rules_spec):
    lint_rules = get_available_lint_rules()

    try:
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

        for lint_rule in self.rules:
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
        return [self.lint_poentry(entry) for entry in po]
