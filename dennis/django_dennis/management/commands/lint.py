import sys

from django.core.management.base import BaseCommand

from dennis.cmdline import cmdline_handler


class Command(BaseCommand):
    help = 'Runs dennis subcommands'

    def run_from_argv(self, argv):
        # Overrides run_from_argv so as to ignore all the option
        # parser stuff. That way the dennis cmdline_handler can do the
        # option parsing and --help works and all that.
        self.execute(*argv)

    def handle(self, *args, **options):
        # We're (ab)using dennis' command line handler so then we
        # don't have to repeat the command line handling. We only want
        # to do linting, though. Also, it turns out args has different
        # stuff in it depend on whether this command is run through
        # call_command() or ./manage.py. So we selectively nix some
        # args ('manage.py' and 'lint') if they're there and if not,
        # we don't worry about it.
        if 'lint' in args:
            args = args[args.index('lint')+1:]

        args = ['lint'] + list(args)

        sys.exit(cmdline_handler('manage.py lint', list(args)))
