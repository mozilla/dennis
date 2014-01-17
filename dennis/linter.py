from collections import namedtuple

import polib

from dennis.tools import VariableTokenizer


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
    name = ''
    desc = ''

    def lint(self, vartok, linted_entry):
        """Takes a linted entry and adds errors and warnings

        :arg vartok: the variable tokenizer to use for tokenizing
            on variable tokens
        :arg linted_entry: the LintedEntry to work on

        """
        raise NotImplemented


class MalformedVarsLintRule(LintRule):
    name = 'malformed'
    desc = 'Checks for malformed variables that cause errors'

    def lint(self, vartok, linted_entry):
        malformed_re = vartok.malformed_vars_re

        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            # For each Var class, we ask it to find malformed
            for var in vartok.vars_:
                malformed = malformed_re.findall(trstr.msgstr_string)
                if not malformed:
                    continue

                malformed = [item.strip() for item in malformed]
                linted_entry.add_error(
                    self.name,
                    trstr,
                    u'malformed variables: {0}'.format(u', '.join(malformed)))


class MismatchedVarsLintRule(LintRule):
    name = 'mismatched'
    desc = 'Checks for variables in one string not in the other'

    def lint(self, vartok, linted_entry):
        for trstr in linted_entry.strs:
            if not trstr.msgstr_string:
                continue

            msgid_tokens = vartok.extract_tokens(' '.join(trstr.msgid_strings))
            msgstr_tokens = vartok.extract_tokens(trstr.msgstr_string)

            missing = msgid_tokens.difference(msgstr_tokens)
            invalid = msgstr_tokens.difference(msgid_tokens)

            if missing:
                linted_entry.add_warning(
                    self.name,
                    trstr,
                    u'missing variables: {0}'.format(u', '.join(sorted(missing))))

            if invalid:
                linted_entry.add_error(
                    self.name,
                    trstr,
                    u'invalid variables: {0}'.format(u', '.join(sorted(invalid))))


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

    # This removes empty strings from the rules_spec.
    rules_spec = [rule for rule in rules_spec if rule]

    if not rules_spec:
        return [rule() for name, rule in lint_rules.items()]

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
        return [
            self.lint_poentry(entry) for entry in po.translated_entries()
        ]
