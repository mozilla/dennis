from dennis.django_dennis.management.commands import DennisBaseCommand


class Command(DennisBaseCommand):
    help = 'Runs dennis subcommands'
    dennis_subcommand = 'lint'
