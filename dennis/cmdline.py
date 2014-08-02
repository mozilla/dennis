import os
import sys
from functools import wraps

import polib

from dennis import __version__
from dennis.linter import Linter, get_available_lint_rules
from dennis.tools import (
    BetterArgumentParser,
    FauxTerminal,
    PY2,
    Terminal,
    get_available_vars
)
from dennis.translator import Translator, get_available_pipeline_parts


USAGE = '%prog [options] [command] [command-options]'
VERSION = 'dennis ' + __version__

# blessings.Terminal and our FauxTerminal don't maintain any state so
# we can make it global
if sys.stdout.isatty():
    TERM = Terminal()
else:
    TERM = FauxTerminal()


def utf8_args(fun):
    @wraps(fun)
    def _utf8_args(*args):
        args = [part.encode('utf-8') for part in args]
        return fun(*args)
    return _utf8_args


def out(*s):
    for part in s:
        sys.stdout.write(part)
    sys.stdout.write('\n')


def err(*s):
    """Prints a single-line string to stderr."""
    sys.stderr.write(TERM.bold_red)
    sys.stderr.write('Error: ')
    for part in s:
        sys.stderr.write(part)
    sys.stderr.write(TERM.normal)
    sys.stderr.write('\n')


if PY2 and not sys.stdout.isatty():
    # If it's Python2 and not a tty, then we need to encode the text
    # type things as utf8 before spitting them out to stdout and
    # stderr.
    out = utf8_args(out)
    err = utf8_args(err)


def build_parser(usage, **kwargs):
    """Builds an OptionParser with the specified kwargs."""
    return BetterArgumentParser(usage=usage, version=VERSION, **kwargs)


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
        '\nAvailable Lint Rules (E for Error, W for Warning):\n' +
        '\n'.join(
            ['  {num:6} {name}: {desc}'.format(num=num, name=cls.name,
                                                desc=cls.desc)
             for num, cls in rules])
    )


def lint_cmd(scriptname, command, argv):
    """Lints a .po file or directory of files."""
    if not '--quiet' in argv and not '-q' in argv:
        out('dennis version {version}'.format(version=__version__))

    parser = build_parser(
        'usage: %prog lint [ DIR | FILENAME <FILENAME> ... ]',
        description='Lints a .po file for mismatched Python string '
        'formatting tokens.',
        epilog='Note: You can ignore rules on a string-by-string basis by '
        'adding an extracted comment "dennis-ignore: <comma-separated-rules>". '
        'See documentation for details.',
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
        default='pysprintf,pyformat')
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
        po_files = args

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
            err('>>> Problem opening file: {fn}'.format(fn=fn))
            err(repr(ioe))
            out('')

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
            out(TERM.bold_green,
                '>>> Working on: {fn}'.format(fn=fn),
                TERM.normal)

        error_count = 0
        warning_count = 0

        for entry in problem_results:
            total_error_count += len(entry.errors)
            error_count += len(entry.errors)

            if not options.quiet:
                # TODO: This is totally shite code.
                for code, trstr, msg in entry.errors:
                    out(TERM.bold_red,
                        code,
                        ': ',
                        msg,
                        TERM.normal)
                    for field, s in zip(trstr.msgid_fields, trstr.msgid_strings):
                        out(field, ' "', s, '"')
                    out(trstr.msgstr_field, ' "', trstr.msgstr_string, '"')
                    out('')

            total_warning_count +=  len(entry.warnings)
            warning_count +=  len(entry.warnings)

            if not options.quiet and not options.errorsonly:
                for code, trstr, msg in entry.warnings:
                    out(TERM.bold_yellow,
                        code,
                        ': ',
                        msg,
                        TERM.normal)
                    for field, s in zip(trstr.msgid_fields, trstr.msgid_strings):
                        out(field, ' "', s, '"')
                    out(trstr.msgstr_field, ' "', trstr.msgstr_string, '"')
                    out('')

        files_to_errors[fn] = (error_count, warning_count)

        if error_count > 0:
            total_files_with_errors += 1

        if not options.quiet:
            out('Totals')
            if not options.errorsonly:
                out('  Warnings: {warnings:5}'.format(warnings=warning_count))
            out('  Errors:   {errors:5}\n'.format(errors=error_count))

    if len(po_files) > 1 and not options.quiet:
        out('Final totals')
        out('  Number of files examined:          {count:5}'.format(
            count=len(po_files)))
        out('  Total number of files with errors: {count:5}'.format(
            count=total_files_with_errors))
        if not options.errorsonly:
            out('  Total number of warnings:          {count:5}'.format(
                count=total_warning_count))
        out('  Total number of errors:            {count:5}'.format(
            count=total_error_count))
        out('')

        file_counts = [
            (counts[0], counts[1], fn.split(os.sep)[-3], fn.split(os.sep)[-1])
            for (fn, counts) in files_to_errors.items()
        ]

        # If we're showing errors only, then don't talk about warnings.
        if options.errorsonly:
            header = 'Errors  Filename'
            line = ' {errors:5}  {locale} ({fn})'
        else:
            header = 'Warnings  Errors  Filename'
            line = ' {warnings:5}     {errors:5}  {locale} ({fn})'

        file_counts = list(reversed(sorted(file_counts)))
        printed_header = False
        for error_count, warning_count, locale, fn in file_counts:
            if not error_count and not warning_count:
                continue
            if not printed_header:
                out(header)
                printed_header = True

            out(line.format(
                warnings=warning_count, errors=error_count, fn=fn,
                locale=locale))

    # Return 0 if everything was fine or 1 if there were errors.
    return 1 if total_error_count else 0


def status_cmd(scriptname, command, argv):
    """Shows status of a .po file."""
    out('{0} version {1}'.format(scriptname, __version__))
    parser = build_parser(
        'usage: %prog status [ DIR | FILENAME <FILENAME> ... ]',
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

    if os.path.isdir(args[0]):
        po_files = []
        for root, dirs, files in os.walk(args[0]):
            po_files.extend(
                [os.path.join(root, fn) for fn in files
                 if fn.endswith('.po')])
    else:
        po_files = args

    for fn in po_files:
        try:
            if not os.path.exists(fn):
                raise IOError('File "{fn}" does not exist.'.format(fn=fn))

            pofile = polib.pofile(fn)
        except IOError as ioe:
            err('>>> Problem opening file: {fn}'.format(fn=fn))
            err(repr(ioe))
            continue

        out('')
        out(TERM.bold_green, '>>> Working on: {fn}'.format(fn=fn), TERM.normal)

        out('Metadata:')
        for key in ('Language', 'Report-Msgid-Bugs-To', 'PO-Revision-Date',
                    'Last-Translator', 'Language-Team', 'Plural-Forms'):
            if key in pofile.metadata and pofile.metadata[key]:
                out('  ', key, ': ', pofile.metadata[key])
        out('')

        if options.showuntranslated:
            out('Untranslated strings:')
            out('')
            for poentry in pofile.untranslated_entries():
                if poentry.comment:
                    out('#. {0}'.format(poentry.comment))
                if poentry.tcomment:
                    out('# {0}'.format(poentry.tcomment))
                if poentry.occurrences:
                    for occ in poentry.occurrences:
                        out('#: {0}:{1}'.format(occ[0], occ[1]))
                if poentry.flags:
                    out('Flags: {0}'.format(poentry.flags))
                out('msgid "{0}"'.format(poentry.msgid))
                if poentry.msgid_plural:
                    out('msgid_plural "{0}"'.format(poentry.msgid_plural))
                out('')

        out('Statistics:')
        out('  # Translated:   {0}'.format(len(pofile.translated_entries())))
        out('  # Fuzzy:        {0}'.format(len(pofile.fuzzy_entries())))
        out('  # Untranslated: {0}'.format(len(pofile.untranslated_entries())))
        if pofile.percent_translated() == 100:
            out('  Percentage:     100% COMPLETE!')
        else:
            out('  Percentage:     {0}%'.format(pofile.percent_translated()))
    return 0


def translate_cmd(scriptname, command, argv):
    """Translate a single string or .po file of strings."""
    if '-' not in argv:
        # Don't print version stuff if we're reading from stdin.
        out('{0} version {1}'.format(scriptname, __version__))

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
        default='pysprintf,pyformat')
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
            data = translator.translate_string(arg)
            if PY2:
                data = data.encode('utf-8')
            print(data)

    elif len(args) == 1 and args[0] == '-':
        # Read everything from stdin, then translate it
        data = translator.translate_string(sys.stdin.read())
        if PY2:
            data = data.encode('utf-8')
        print(data)

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
    out('{0} version {1}'.format(scriptname, __version__))

    handlers = get_handlers()

    parser = build_parser("%prog [command]")
    parser.print_help()
    out('')
    out('Commands:')
    for command_str, _, command_help in handlers:
        out('  {cmd:10}  {hlp}'.format(cmd=command_str, hlp=command_help))


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
