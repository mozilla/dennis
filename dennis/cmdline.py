import os
import sys

import polib

from dennis import __version__
from dennis.linter import Linter, get_available_lint_rules
from dennis.tools import BetterArgumentParser, Terminal, get_available_vars
from dennis.translator import Translator, get_available_pipeline_parts


USAGE = '%prog [options] [command] [command-options]'
VERSION = 'dennis ' + __version__

# blessings.Terminal and our mock Terminal don't maintain any state
# so we can just make it global
TERMINAL = Terminal()


def print_utf8(s):
    print s.encode('utf-8')


def build_parser(usage, **kwargs):
    """Builds an OptionParser with the specified kwargs."""
    return BetterArgumentParser(usage=usage, version=VERSION, **kwargs)


def err(s):
    """Prints a single-line string to stderr."""
    sys.stderr.write('Error: ' + s + '\n')


def format_vars():
    vars_ = sorted(get_available_vars().items())
    return (
        '\nAvailable Variable Formats:\n' +
        '\n'.join(
            ['  {name:13}  {desc}'.format(name=name, desc=cls.desc)
             for name, cls in vars_])
    )


def format_pipeline_parts():
    parts = sorted(get_available_pipeline_parts().items())
    return (
        '\nAvailable Pipeline Parts:\n' +
        '\n'.join(
            ['  {name:13}  {desc}'.format(name=name, desc=cls.desc)
             for name, cls in parts])
    )


def format_lint_rules():
    rules = sorted(get_available_lint_rules().items())
    return (
        '\nAvailable Lint Rules:\n' +
        '\n'.join(
            ['  {name:13}  {desc}'.format(name=name, desc=cls.desc)
             for name, cls in rules])
    )


def lint_cmd(scriptname, command, argv):
    """Lints a .po file or directory of files."""
    if not '--quiet' in argv and not '-q' in argv:
        print 'dennis version {version}'.format(version=__version__)

    parser = build_parser(
        'usage: %prog lint [ FILE | DIR ]',
        description='Lints a .po file for mismatched Python string '
        'formatting tokens.',
        sections=[
            (format_vars(), True),
            (format_lint_rules(), True),
        ])
    parser.add_option(
        '--vars',
        dest='vars',
        help=('Comma-separated list of variable types. See Available Variable '
              'Formats.'),
        metavar='VARS',
        default='python')
    parser.add_option(
        '--rules',
        dest='rules',
        help=('Comma-separated list of lint rules to use. Defaults to all '
              'rules. See Available Lint Rules.'),
        metavar='RULES',
        default='')
    parser.add_option(
        '-q', '--quiet',
        action='store_true',
        dest='quiet',
        help='quiet all output')
    parser.add_option(
        '--errorsonly',
        action='store_true',
        dest='errorsonly',
        help='only print errors')

    (options, args) = parser.parse_args(argv)

    if not args:
        parser.print_help()
        return 1

    linter = Linter(options.vars.split(','), options.rules.split(','))

    if os.path.isdir(args[0]):
        po_files = []
        for root, dirs, files in os.walk(args[0]):
            po_files.extend(
                [os.path.join(root, fn) for fn in files
                 if fn.endswith('.po')])

    else:
        po_files = [args[0]]

    po_files = [os.path.abspath(fn) for fn in po_files if fn.endswith('.po')]

    files_to_errors = {}
    total_error_count = 0
    total_warning_count = 0
    total_files_with_errors = 0

    for fn in po_files:
        try:
            if not os.path.exists(fn):
                raise IOError('File "{fn}" does not exist.'.format(fn=fn))

            results = linter.verify_file(fn)

        except IOError as ioe:
            # This is not a valid .po file. So mark it as an error.
            print TERMINAL.bold_red('>>> Error opening file: {fn}'.format(
                    fn=fn))
            print TERMINAL.bold_red(ioe.message)
            print ''

            # FIXME - should we track this separately as an invalid
            # file?
            files_to_errors[fn] = (1, 0)
            total_error_count += 1
            continue

        # Extract all the problematic LintItems--they have non-empty
        # missing or invalid lists.
        problem_results = [
            r for r in results if r.has_problems(options.errorsonly)]

        # We don't want to print output for files that are fine, so we
        # update the bookkeeping and move on.
        if not problem_results:
            files_to_errors[fn] = (0, 0)
            continue

        if not options.quiet:
            print TERMINAL.bold_green('>>> Working on: {fn}'.format(fn=fn))

        output = []
        error_count = 0
        warning_count = 0

        for entry in problem_results:
            total_error_count += len(entry.errors)
            error_count += len(entry.errors)

            if not options.quiet:
                # TODO: This is totally shite code.
                for code, trstr, msg in entry.errors:
                    output.append(TERMINAL.bold_red(u'Error: {0}: {1}'.format(
                        code, msg)))
                    for field, s in zip(trstr.msgid_fields, trstr.msgid_strings):
                        output.append(u'{0} "{1}"'.format(field, s))
                    output.append(u'{0} "{1}"\n'.format(
                            trstr.msgstr_field, trstr.msgstr_string))

            total_warning_count +=  len(entry.warnings)
            warning_count +=  len(entry.warnings)

            if not options.quiet and not options.errorsonly:
                for code, trstr, msg in entry.warnings:
                    output.append(TERMINAL.bold_yellow(u'Warning: {0}: {1}'.format(
                                code, msg)))
                    for field, s in zip(trstr.msgid_fields, trstr.msgid_strings):
                        output.append(u'{0} "{1}"'.format(field, s))
                    output.append(u'{0} "{1}"\n'.format(
                        trstr.msgstr_field, trstr.msgstr_string))

        files_to_errors[fn] = (error_count, warning_count)

        if error_count > 0:
            total_files_with_errors += 1

        if not options.quiet:
            output.append(u'Totals')
            if not options.errorsonly:
                output.append(u'  Warnings: {warnings:5}'.format(warnings=warning_count))
            output.append(u'  Errors:   {errors:5}\n'.format(errors=error_count))

        print_utf8(u'\n'.join(output))

    if len(po_files) > 1 and not options.quiet:
        print 'Final totals'
        print '  Number of files examined:          {count:5}'.format(
            count=len(po_files))
        print '  Total number of files with errors: {count:5}'.format(
            count=total_files_with_errors)
        if not options.errorsonly:
            print '  Total number of warnings:          {count:5}'.format(
                count=total_warning_count)
        print '  Total number of errors:            {count:5}'.format(
            count=total_error_count)
        print ''

        file_counts = [
            (counts[0], counts[1], fn.split(os.sep)[-3], fn.split(os.sep)[-1])
            for (fn, counts) in files_to_errors.items()]

        # If we're showing errors only, then don't talk about warnings.
        if options.errorsonly:
            header = 'Errors  Filename'
            line = ' {errors:5}  {locale} ({fn})'
        else:
            header = 'Warnings  Errors  Filename'
            line = ' {warnings:5}     {errors:5}  {locale} ({fn})'

        print header
        file_counts = reversed(sorted(file_counts))
        for error_count, warning_count, locale, fn in file_counts:
            if not error_count and not warning_count:
                continue

            print line.format(
                warnings=warning_count, errors=error_count, fn=fn,
                locale=locale)

    # Return 0 if everything was fine or 1 if there were errors.
    return 1 if total_error_count else 0


def status_cmd(scriptname, command, argv):
    """Shows status of a .po file."""
    print 'dennis version {version}'.format(version=__version__)
    parser = build_parser(
        'usage: %prog status FILENAME',
        description='Shows status of a .po file.')
    parser.add_option(
        '--showuntranslated',
        action='store_true',
        dest='showuntranslated',
        help='show untranslated strings')

    (options, args) = parser.parse_args(argv)

    if not args:
        parser.print_help()
        return 1

    fn = args[0]

    if not os.path.exists(fn):
        raise IOError('File "{0}" does not exist.'.format(fn))

    pofile = polib.pofile(fn)

    print ''
    print 'File: {0}'.format(fn)
    print ''

    if options.showuntranslated:
        print 'Untranslated strings:'
        print ''
        for poentry in pofile.untranslated_entries():
            if poentry.comment:
                print 'Comment: {0}'.format(poentry.comment)
            if poentry.tcomment:
                print 'Translator comment: {0}'.format(poentry.tcomment)
            if poentry.flags:
                print 'Flags: {0}'.format(poentry.flags)
            print 'msgid "{0}"'.format(poentry.msgid)
            if poentry.msgid_plural:
                print 'msgid_plural "{0}"'.format(poentry.msgid_plural)
            print ''
        print '--'

    print 'Metadata:'
    for key in ('Report-Msgid-Bugs-To', 'PO-Revision-Date', 'Last-Translator',
                'Language-Team', 'Language', 'Plural-Forms'):
        if key in pofile.metadata and pofile.metadata[key]:
            print '  {0}: {1}'.format(key, pofile.metadata[key])
    print ''
    print '--'

    print 'Statistics:'
    print '  # Translated:   {0}'.format(len(pofile.translated_entries()))
    print '  # Fuzzy:        {0}'.format(len(pofile.fuzzy_entries()))
    print '  # Untranslated: {0}'.format(len(pofile.untranslated_entries()))
    print '  Percentage:     {0}'.format(pofile.percent_translated())
    return 0


def translate_cmd(scriptname, command, argv):
    """Translate a single string or .po file of strings."""
    if '-' not in argv:
        # Don't print version stuff if we're reading from stdin.
        print '%s version %s' % (scriptname, __version__)

    parser = build_parser(
        'usage: %prog tramslate '
        '[- | -s STRING <STRING> ... | FILENAME <FILENAME> ...]',
        description='Translates a string or a .po file into Pirate.',
        epilog='Note: Translating files is done in-place replacing '
        'the original file.',
        sections=[
            (format_vars(), True),
            (format_pipeline_parts(), True),
        ])
    parser.add_option(
        '--vars',
        dest='vars',
        help=('Comma-separated list of variable types. See Available Variable '
              'Formats.'),
        metavar='VARS',
        default='python')
    parser.add_option(
        '-p', '--pipeline',
        dest='pipeline',
        help='Translate pipeline. See Available Pipeline Parts.',
        metavar='PIPELINE',
        default='html,pirate')
    parser.add_option(
        '-s', '--string',
        action='store_true',
        dest='strings',
        help='translates specified string args')

    (options, args) = parser.parse_args(argv)

    if not args:
        parser.print_help()
        return 1

    translator = Translator(
        options.vars.split(','), options.pipeline.split(','))

    if options.strings:
        # Args are strings to be translated
        for arg in args:
            print_utf8(translator.translate_string(arg))

    elif len(args) == 1 and args[0] == '-':
        # Read everything from stdin, then translate it
        print_utf8(translator.translate_string(sys.stdin.read()))

    else:
        # Args are filenames
        for arg in args:
            translator.translate_file(arg)

    return 0


def get_handlers():
    handlers = [(name.replace('_cmd', ''), fun, fun.__doc__)
                for name, fun in globals().items()
                if name.endswith('_cmd')]
    return handlers


def print_help(scriptname):
    print '%s version %s' % (scriptname, __version__)

    handlers = get_handlers()

    parser = build_parser("%prog [command]")
    parser.print_help()
    print ''
    print 'Commands:'
    for command_str, _, command_help in handlers:
        print '  {cmd:10}  {hlp}'.format(cmd=command_str, hlp=command_help)


def cmdline_handler(scriptname, argv):
    handlers = get_handlers()

    if not argv or argv[0] in ('-h', '--help'):
        print_help(scriptname)
        return 0

    if '--version' in argv:
        # We've already printed the version, so we can just exit.
        return 0

    command = argv.pop(0)
    for (cmd, fun, hlp) in handlers:
        if cmd == command:
            return fun(scriptname, command, argv)

    err('Command "{0}" does not exist.'.format(command))
    print_help(scriptname)

    return 1
