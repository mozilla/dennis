from collections import namedtuple

import polib

from dennis.tools import VariableTokenizer, all_subclasses, parse_dennis_note


IdString = namedtuple('IdString', ('msgid_fields', 'msgid_strings'))


class LintedEntry(object):
    def __init__(self, poentry):
        self.poentry = poentry
        self.msgid = poentry.msgid

        if poentry.msgid_plural:
            msgid_fields = ('msgid', 'msgid_plural')
            msgid_strings = (poentry.msgid, poentry.msgid_plural)
        else:
            msgid_fields = ('msgid',)
            msgid_strings = (poentry.msgid,)

        self.str = IdString(msgid_fields, msgid_strings)

        self.warnings = []

    def add_warning(self, code, idstr, msg):
        self.warnings.append((code, idstr, msg))

    def has_problems(self):
        return bool(self.warnings)


class TemplateLintRule(object):
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


class HardToReadNamesTLR(TemplateLintRule):
    num = 'W500'
    name = 'hardtoread'
    desc = 'Looks for variables that are hard to read like o, O, 0, l, 1'

    hard_to_read = ('o', 'O', '0', 'l', '1')

    def lint(self, vartok, linted_entry):
        idstr = linted_entry.str

        for s in idstr.msgid_strings:
            if not s:
                continue

            msgid_tokens = vartok.extract_tokens(s)
            msgid_tokens = [vartok.extract_variable_name(token)
                            for token in msgid_tokens]

            for token in msgid_tokens:
                if token in self.hard_to_read:
                    linted_entry.add_warning(
                        self.num,
                        idstr,
                        u'hard to read variable name "{0}"'.format(
                            token))


class OneCharNamesTLR(TemplateLintRule):
    num = 'W501'
    name = 'onechar'
    desc = 'Looks for one character variable names'

    def lint(self, vartok, linted_entry):
        idstr = linted_entry.str

        for s in idstr.msgid_strings:
            if not s:
                continue

            msgid_tokens = vartok.extract_tokens(s)
            msgid_tokens = [vartok.extract_variable_name(token)
                            for token in msgid_tokens]

            for token in msgid_tokens:
                if len(token) == 1 and token.isalpha():
                    linted_entry.add_warning(
                        self.num,
                        idstr,
                        u'one character variable name "{0}"'.format(
                            token))


class MultipleUnnamedVarsTLR(TemplateLintRule):
    num = 'W502'
    name = 'unnamed'
    desc = 'Looks for multiple unnamed variables'

    def lint(self, vartok, linted_entry):
        idstr = linted_entry.str

        for s in idstr.msgid_strings:
            if not s:
                continue

            msgid_tokens = vartok.extract_tokens(s, unique=False)
            msgid_tokens = [vartok.extract_variable_name(token)
                            for token in msgid_tokens]

            if msgid_tokens.count('') > 1:
                linted_entry.add_warning(
                    self.num,
                    idstr,
                    u'multiple variables with no name.')


def get_available_lint_rules(name_and_num=False):
    lint_rules = {}

    for cls in all_subclasses(TemplateLintRule):
        if cls.num:
            lint_rules[cls.num] = cls
            if name_and_num and cls.name:
                lint_rules[cls.name] = cls

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


class TemplateLinter(object):
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
            self.lint_poentry(entry) for entry in po
        ]
