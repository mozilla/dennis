import os
import sys

from dennis import __version__
from dennis.linter import Linter, format_with_errors
from dennis.tools import BetterArgumentParser, Terminal, get_types
from dennis.translator import Translator, get_available_pipeline_parts


USAGE = '%prog [options] [command] [command-options]'
VERSION = '%prog ' + __version__

# blessings.Terminal and our mock Terminal don't maintain any state
# so we can just make it global
TERMINAL = Terminal()


def build_parser(usage, **kwargs):
    """Builds an OptionParser with the specified kwargs."""
    return BetterArgumentParser(usage=usage, version=VERSION, **kwargs)


def err(s):
    """Prints a single-line string to stderr."""
    sys.stderr.write('Error: ' + s + '\n')


def format_types():
    return (
        '\nAvailable Types:\n' +
        '\n'.join(
            ['  {name:10}  {desc}'.format(name=name, desc=desc)
             for name, desc in get_types()])
    )


def format_pipeline_parts():
    parts = sorted(get_available_pipeline_parts().items())
    return (
        '\nAvailable Pipeline Parts:\n' +
        '\n'.join(
            ['  {name:10}  {desc}'.format(name=name, desc=cls.__doc__)
             for name, cls in parts])
    )


def print_lint_error(vartok, lint_error):
    """Prints a LintError to stdout

    :arg vartok: VariableTokenizer instance
    :arg lint_error: a LintError to print

    Prints it to stdout. It also colorizes it using blessings
    if blessings is available.
    """
    if lint_error.invalid:
        print u'{label}: {tokens}'.format(
            label=TERMINAL.bold_red('Error: invalid tokens'),
            tokens=', '.join(lint_error.invalid))

    if lint_error.missing:
        print u'{label}: {tokens}'.format(
            label=TERMINAL.bold_yellow('Warning: missing tokens'),
            tokens=u', '.join(lint_error.missing))

    name = TERMINAL.yellow('msgid')
    print u'{0}: "{1}"'.format(name, lint_error.msgid)

    if lint_error.index is not None:
        # Print the plural
        name = TERMINAL.yellow('msgid_plural')
        print u'{0}: "{1}"'.format(name, lint_error.msgid_text)

    # Print the translated string with token errors
    if lint_error.index is not None:
        name = 'msgstr[{index}]'.format(index=lint_error.index)
    else:
        name = 'msgstr'
    print u'{0}: "{1}"'.format(
        TERMINAL.yellow(name),
        format_with_errors(
            TERMINAL, vartok, lint_error.msgstr_text, lint_error.msgid_tokens))

    print ''


def lint_cmd(scriptname, command, argv):
    """Lints a .po file or directory of files."""
    if not '--quiet' in argv:
        print '%s version %s' % (scriptname, __version__)

    parser = build_parser(
        'usage: %prog lint [ FILE | DIR ]',
        description='Lints a .po file for mismatched Python string '
        'formatting tokens.',
        sections=[
            (format_types(), True),
        ])
    parser.add_option(
        '-t', '--types',
        dest='types',
        help='Comma-separated list of variable types. See Available Types.',
        metavar='TYPES',
        default='python')
    parser.add_option(
        '-q', '--quiet',
        action='store_true',
        dest='quiet',
        help='quiet all output')

    (options, args) = parser.parse_args(argv)

    if not args:
        parser.print_help()
        return 1

    linter = Linter(options.types.split(','))

    if os.path.isdir(args[0]):
        po_files = []
        for root, dirs, files in os.walk(args[0]):
            po_files.extend(
                [os.path.join(root, fn) for fn in files
                 if fn.endswith('.po')])

    else:
        po_files = [args[0]]

    files_to_errors = {}
    total_error_count = 0
    total_warning_count = 0
    total_files_with_errors = 0

    for fn in po_files:
        if not fn.endswith('.po'):
            continue

        fn = os.path.abspath(fn)

        results = linter.verify_file(fn)

        # This is the total number of strings examined.
        count = len(results)

        # Extract all the problematic LintItems--they have non-empty
        # missing or invalid lists.
        problem_results = [r for r in results if r.missing or r.invalid]

        # We don't want to print output for files that are fine, so we
        # update the bookkeeping and move on.
        if not problem_results:
            files_to_errors[fn] = (0, 0)
            continue

        if not options.quiet:
            print TERMINAL.bold_green('>>> Working on: {fn}'.format(fn=fn))

        error_count = 0
        warning_count = 0
        for result in problem_results:
            if not result:
                continue

            if result.invalid:
                total_error_count += 1
                error_count += 1
            if result.missing:
                total_warning_count += 1
                warning_count += 1

            if not options.quiet:
                print_lint_error(linter.vartok, result)

        files_to_errors[fn] = (error_count, warning_count)

        if error_count > 0:
            total_files_with_errors += 1

        if not options.quiet:
            print (
                'Total: {count:5}  Warnings: {warnings:5}  Errors: {errors:5}'
                .format(count=count, warnings=warning_count, errors=error_count))
            print ''

    if len(po_files) > 1 and not options.quiet:
        print 'Final Tally:'
        print ''

        print 'Number of files examined:          {count:5}'.format(
            count=len(po_files))
        print 'Total number of files with errors: {count:5}'.format(
            count=total_files_with_errors)
        print 'Total number of warnings:          {count:5}'.format(
            count=total_warning_count)
        print 'Total number of errors:            {count:5}'.format(
            count=total_error_count)
        print ''

        file_counts = [
            (counts[0], counts[1], fn.split(os.sep)[-3], fn.split(os.sep)[-1])
            for (fn, counts) in files_to_errors.items()]

        print 'Warnings  Errors  Filename'
        file_counts = reversed(sorted(file_counts))
        for error_count, warning_count, locale, fn in file_counts:
            if not error_count and not warning_count:
                continue

            print ' {warnings:5}     {errors:5}  {locale} ({fn})'.format(
                warnings=warning_count, errors=error_count, fn=fn,
                locale=locale)

    # Return 0 if everything was fine or 1 if there were errors.
    return 1 if total_error_count else 0


def translate_cmd(scriptname, command, argv):
    """Translate a single string or .po file of strings."""
    print '%s version %s' % (scriptname, __version__)

    parser = build_parser(
        'usage: %prog tramslate '
        '[-s STRING <STRING> ... | FILENAME <FILENAME> ...]',
        description='Translates a string or a .po file into Pirate.',
        epilog='Note: Translating files is done in-place replacing '
        'the original file.',
        sections=[
            (format_types(), True),
            (format_pipeline_parts(), True),
        ])
    # FIXME: move printing of available types to epilog. also rename
    # types to something more accurate like "variable formats".
    parser.add_option(
        '-t', '--types',
        dest='types',
        help='Comma-separated list of variable types. See Available Types.',
        metavar='TYPES',
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
        options.types.split(','), options.pipeline.split(','))

    if options.strings:
        for arg in args:
            print translator.translate_string(arg)
        return 0

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
