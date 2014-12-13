import sys

from django.core.management.base import BaseCommand

from dennis.cmdline import click_run


class DennisBaseCommand(BaseCommand):
    """Handles the shenanigans we do to make this work

    Make sure to set class properties:

    * help
    * dennis_subcommand

    """

    def run_from_argv(self, argv):
        # Overrides run_from_argv so as to ignore all the option
        # parser stuff. That way the dennis cli can do the option
        # parsing and --help works and all that.
        self.execute(*argv)

    def handle(self, *args, **options):
        # The dennis command line handler already has all the option
        # and argument parsing. So rather than repeat that here, we
        # rebuild sys.argv and then invoke the Dennis cli.
        #
        # Also, it turns out args has different stuff in it depend on
        # whether this command is run through call_command() or
        # ./manage.py. So we selectively nix some args ('manage.py'
        # and the subcommand) if they're there and if not, we don't worry
        # about it.
        if self.dennis_subcommand in args:
            args = args[args.index(self.dennis_subcommand)+1:]

        args = ['dennis', self.dennis_subcommand] + list(args)
        sys.argv = args
        click_run()
