import sys

from django.core.management.base import BaseCommand

from dennis.cmdline import cmdline_handler


class DennisBaseCommand(BaseCommand):
    """Handles the shenanigans we do to make this work

    Make sure to set class properties:

    * help
    * dennis_subcommand

    """

    def run_from_argv(self, argv):
        # Overrides run_from_argv so as to ignore all the option
        # parser stuff. That way the dennis cmdline_handler can do the
        # option parsing and --help works and all that.
        self.execute(*argv)

    def handle(self, *args, **options):
        # The dennis command line handler already has all the option
        # and argument parsing. So rather than repeat that here, we
        # tweak some arguments and then pass it through to the dennis
        # command line handler.
        # 
        # Also, it turns out args has different stuff in it depend on
        # whether this command is run through call_command() or
        # ./manage.py. So we selectively nix some args ('manage.py'
        # and the subcommand) if they're there and if not, we don't worry
        # about it.
        if self.dennis_subcommand in args:
            args = args[args.index(self.dennis_subcommand)+1:]

        args = [self.dennis_subcommand] + list(args)

        sys.exit(cmdline_handler('manage.py ' + self.dennis_subcommand, args))
