from dennis.tools import (
    VariableTokenizer,
    all_subclasses,
    parse_dennis_note,
    parse_pofile
)
from dennis.linter import (
    LintedEntry,
    LintMessage
)


WARNING = 'warn'
ERROR = 'err'


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
    desc = 'Looks for vars that are hard to read like o, O, 0, l, 1'

    hard_to_read = ('o', 'O', '0', 'l', '1')

    def lint(self, vartok, linted_entry):
        msgs = []

        idstr = linted_entry.str

        for s in idstr.msgid_strings:
            if not s:
                continue

            msgid_tokens = vartok.extract_tokens(s)
            msgid_tokens = [vartok.extract_variable_name(token)
                            for token in msgid_tokens]

            for token in msgid_tokens:
                if token in self.hard_to_read:
                    msgs.append(
                        LintMessage(
                            WARNING, linted_entry.poentry.linenum, 0, self.num,
                            u'hard to read variable name "{0}"'.format(
                                token),
                            linted_entry.poentry)
                    )
        return msgs


class OneCharNamesTLR(TemplateLintRule):
    num = 'W501'
    name = 'onechar'
    desc = 'Looks for one character variable names'

    def lint(self, vartok, linted_entry):
        msgs = []
        idstr = linted_entry.str

        for s in idstr.msgid_strings:
            if not s:
                continue

            msgid_tokens = vartok.extract_tokens(s)
            msgid_tokens = [vartok.extract_variable_name(token)
                            for token in msgid_tokens]

            for token in msgid_tokens:
                if len(token) == 1 and token.isalpha():
                    msgs.append(
                        LintMessage(
                            WARNING, linted_entry.poentry.linenum, 0, self.num,
                            u'one character variable name "{0}"'.format(
                                token),
                            linted_entry.poentry)
                    )
        return msgs


class MultipleUnnamedVarsTLR(TemplateLintRule):
    num = 'W502'
    name = 'unnamed'
    desc = 'Looks for multiple unnamed variables'

    def lint(self, vartok, linted_entry):
        msgs = []
        idstr = linted_entry.str

        for s in idstr.msgid_strings:
            if not s:
                continue

            msgid_tokens = vartok.extract_tokens(s, unique=False)
            msgid_tokens = [vartok.extract_variable_name(token)
                            for token in msgid_tokens]

            if msgid_tokens.count('') > 1:
                msgs.append(
                    LintMessage(
                        WARNING, linted_entry.poentry.linenum, 0, self.num,
                        u'multiple variables with no name.',
                        linted_entry.poentry)
                )
        return msgs


def get_lint_rules(with_names=False):
    lint_rules = {}

    for cls in all_subclasses(TemplateLintRule):
        if cls.num:
            lint_rules[cls.num] = cls
            if with_names and cls.name:
                lint_rules[cls.name] = cls

    return lint_rules


def convert_rules(rules_spec):
    lint_rules = get_lint_rules(with_names=True)
    rules = [lint_rules[rule]() for rule in rules_spec if rule in lint_rules]
    return rules


class TemplateLinter(object):
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
            if skip == '*' or lint_rule.num in skip:
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
            msgs.extend(self.lint_poentry(entry))
        return msgs
