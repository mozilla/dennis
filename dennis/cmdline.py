import os
import os.path
import sys
from optparse import OptionParser

from dennis import __version__
from dennis.translater import translate_string, translate_file
from dennis.linter import verify_directory, verify_file


USAGE = '%prog [options] [command] [command-options]'
VERSION = '%prog ' + __version__


def build_parser(usage, **kwargs):
    return OptionParser(usage=usage, version=VERSION, **kwargs)


def err(s):
    sys.stderr.write(s + '\n')


def lint(command, argv):
    parser = build_parser(
        'usage: %prog lint [ FILE | DIR ]',
        description='Lints a .po file for mismatched Python string '
        'formatting tokens.')

    (options, args) = parser.parse_args(argv)

    if not args:
        parser.print_help()
        return 1

    if os.path.isdir(args[0]):
        return verify_directory(args[0])

    # Return 0 if everything was fine or 1 if there were errors.
    return verify_file(args[0]) != 0


def translate(command, argv):
    parser = build_parser(
        'usage: %prog tramslate [-s STRING <STRING> ... | FILENAME <FILENAME> ...]',
        description='Translates a string or a .po file into Pirate.',
        epilog='Note: Translating files is done in-place replacing the original '
        'file.')
    parser.add_option(
        '-s', '--string',
        action='store_true',
        dest='strings',
        help='translates specified string args')

    (options, args) = parser.parse_args(argv)

    if not args:
        parser.print_help()
        return 1

    if options.strings:
        for arg in args:
            print translate_string(arg)
        return 0

    for arg in args:
        translate_file(arg)
    return 0


HANDLERS = (
    ('lint', lint, 'Lints a .po file or directory of files.'),
    ('translate', translate, 'Translate a string or file.'),
    )


def cmdline_handler(scriptname, argv):
    print '%s version %s' % (scriptname, __version__)

    # TODO: Rewrite using subparsers.
    handlers = HANDLERS

    if not argv or argv[0] in ('-h', '--help'):
        parser = build_parser("%prog [command]")
        parser.print_help()
        print ''
        print 'Commands:'
        for command_str, _, command_help in handlers:
            print '    %-14s %s' % (command_str, command_help)
        return 0

    if '--version' in argv:
        # We've already printed the version, so we can just exit.
        return 0

    command = argv.pop(0)
    for (cmd, fun, hlp) in handlers:
        if cmd == command:
            return fun(command, argv)

    err('Command "{0}" does not exist.'.format(command))
    for cmd, fun, hlp in handlers:
        err('    %-14s %s' % (cmd, hlp))
    return 1
