import os
import sys
import traceback
from functools import wraps
from textwrap import dedent

import click

from dennis import __version__
from dennis.linter import Linter
from dennis.linter import get_lint_rules as get_linter_rules
from dennis.templatelinter import TemplateLinter
from dennis.templatelinter import get_lint_rules as get_template_linter_rules
from dennis.tools import (
    get_available_formats,
    parse_pofile,
    withlines,
)
from dennis.translator import get_available_pipeline_parts, InvalidPipeline, Translator


USAGE = "%prog [options] [command] [command-options]"
VERSION = "dennis " + __version__


def utf8_args(fun):
    @wraps(fun)
    def _utf8_args(*args):
        args = [part.encode("utf-8") for part in args]
        return fun(*args)

    return _utf8_args


def err(s):
    """Prints a single-line string to stderr."""
    click.secho(f"Error: {s}", fg="red", bold=True, err=True)


def format_formats():
    formats = sorted(get_available_formats().items())
    lines = ["Available Variable Formats:", "", "\b"]
    lines.extend(
        ["{name:19}  {desc}".format(name=name, desc=cls.desc) for name, cls in formats]
    )

    text = "\n".join(lines) + "\n"
    return text


def format_pipeline_parts():
    parts = sorted(get_available_pipeline_parts().items())
    lines = ["Available Pipeline Parts:", "", "\b"]
    lines.extend(
        ["{name:13}  {desc}".format(name=name, desc=cls.desc) for name, cls in parts]
    )
    text = "\n".join(lines) + "\n"
    return text


def format_lint_rules():
    from dennis.linter import get_lint_rules

    rules = sorted(get_lint_rules().items())
    lines = ["Available Lint Rules:", "", "\b"]
    lines.extend(
        [
            "{num:6} {name}: {desc}".format(num=num, name=cls.name, desc=cls.desc)
            for num, cls in rules
        ]
    )
    text = "\n".join(lines) + "\n"
    return text


def format_lint_template_rules():
    from dennis.templatelinter import get_lint_rules

    rules = sorted(get_lint_rules().items())
    lines = ["Available Template Lint Rules:", "", "\b"]
    lines.extend(
        [
            "{num:6} {name}: {desc}".format(num=num, name=cls.name, desc=cls.desc)
            for num, cls in rules
        ]
    )
    text = "\n".join(lines) + "\n"
    return text


def epilog(docstring):
    """Fixes the docstring so it displays properly

    I have problems with docstrings and indentation showing up right
    in click. This fixes that. Plus it allows me to add dynamically
    generated bits to the docstring.

    """

    def _epilog(fun):
        fun.__doc__ = dedent(fun.__doc__) + docstring
        return fun

    return _epilog


def click_run():
    sys.excepthook = exception_handler
    cli(obj={})


@click.group()
def cli():
    pass


@cli.command()
@click.option("--quiet/--no-quiet", default=False)
@click.option(
    "--varformat",
    default="python-format,python-brace-format",
    help=(
        "Comma-separated list of variable formats. " "See Available Variable Formats."
    ),
)
@click.option(
    "--rules",
    default="",
    help=(
        "Comma-separated list of lint rules to use. "
        "Defaults to all rules. See Available Lint Rules."
    ),
)
@click.option(
    "--excluderules",
    default="",
    help=(
        "Comma-separated list of lint rules to exclude. "
        "Defaults to no rules excluded. See Available Lint Rules."
    ),
)
@click.option("--reporter", default="", help="Reporter to use for output.")
@click.option("--errorsonly/--no-errorsonly", default=False, help="Only print errors.")
@click.argument("path", nargs=-1)
@click.pass_context
@epilog(
    format_formats() + "\n" + format_lint_rules() + "\n" + format_lint_template_rules()
)
def lint(ctx, quiet, varformat, rules, excluderules, reporter, errorsonly, path):
    """
    Lints .po/.pot files for issues

    You can ignore rules on a string-by-string basis by adding an
    extracted comment "dennis-ignore: <comma-separated-rules>".  See
    documentation for details.

    """
    if not quiet:
        click.echo(f"dennis version {__version__}")

    # Make sure requested rules are valid
    all_rules = get_linter_rules(with_names=True)
    all_rules.update(get_template_linter_rules(with_names=True))
    rules = [rule.strip() for rule in rules.split(",") if rule.strip()]
    invalid_rules = [rule for rule in rules if rule not in all_rules]
    if invalid_rules:
        raise click.UsageError("invalid rules: %s." % ", ".join(invalid_rules))

    if not rules:
        rules = get_linter_rules()
        rules.update(get_template_linter_rules())
        rules = rules.keys()

    if excluderules:
        excludes = [rule.strip() for rule in excluderules.split(",") if rule.strip()]
        invalid_rules = [rule for rule in excludes if rule not in all_rules]
        if invalid_rules:
            raise click.UsageError(
                "invalid exclude rules: %s." % ", ".join(invalid_rules)
            )

        # Remove excluded rules
        rules = [rule for rule in rules if rule not in excludes]

    # Build linters and lint
    linter = Linter(varformat.split(","), rules)
    templatelinter = TemplateLinter(varformat.split(","), rules)

    po_files = []
    for item in path:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                po_files.extend(
                    [
                        os.path.join(root, fn)
                        for fn in files
                        if fn.endswith((".po", ".pot"))
                    ]
                )
        else:
            po_files.append(item)

    po_files = [os.path.abspath(fn) for fn in po_files if fn.endswith((".po", ".pot"))]

    if not po_files:
        raise click.UsageError("nothing to work on. Use --help for help.")

    files_to_errors = {}
    total_error_count = 0
    total_warning_count = 0
    total_files_with_errors = 0

    for fn in po_files:
        formatted_fn = click.format_filename(fn)
        try:
            if not os.path.exists(fn):
                raise click.UsageError(f'File "{formatted_fn}" does not exist.')

            if fn.endswith(".po"):
                results = linter.verify_file(fn)
            else:
                results = templatelinter.verify_file(fn)
        except IOError as ioe:
            # This is not a valid .po file. So mark it as an error.
            err(f">>> Problem opening file: {formatted_fn}")
            err(repr(ioe))
            click.echo("")

            # FIXME - should we track this separately as an invalid
            # file?
            files_to_errors[fn] = (1, 0)
            total_error_count += 1
            continue

        if errorsonly:
            # Go through and nix all the non-error LintMessages
            results = [res for res in results if res.kind == "err"]

        # We don't want to print output for files that are fine, so we
        # update the bookkeeping and move on.
        if not results:
            files_to_errors[fn] = (0, 0)
            continue

        if not quiet and not reporter:
            click.secho(f">>> Working on: {formatted_fn}", fg="green", bold=True)

        error_results = [res for res in results if res.kind == "err"]
        warning_results = [res for res in results if res.kind == "warn"]

        error_count = len(error_results)
        total_error_count += error_count

        warning_count = len(warning_results)
        total_warning_count += warning_count

        if not quiet:
            for msg in error_results:
                if reporter == "line":
                    click.echo(f"{fn}: {msg.poentry.linenum}: 0: {msg.code}: {msg.msg}")
                else:
                    err(f"{msg.code}: {msg.msg}")
                    click.echo(withlines(msg.poentry.linenum, msg.poentry.original))
                    click.echo("")

        if not quiet and not errorsonly:
            for msg in warning_results:
                if reporter == "line":
                    click.echo(f"{fn}: {msg.poentry.linenum}: 0: {msg.code}: {msg.msg}")
                else:
                    click.secho(f"{msg.code}: {msg.msg}", fg="yellow", bold=True)
                    click.echo(withlines(msg.poentry.linenum, msg.poentry.original))
                    click.echo("")

        files_to_errors[fn] = (error_count, warning_count)

        if error_count > 0:
            total_files_with_errors += 1

        if not quiet and reporter != "line":
            click.echo("Totals")
            if not errorsonly:
                click.echo(f"  Warnings: {warning_count:5}")
            click.echo(f"  Errors:   {error_count:5}")
            click.echo("")

    if len(po_files) > 1 and not quiet and reporter != "line":
        click.echo("Final totals")
        click.echo(f"  Number of files examined:          {len(po_files):5}")
        click.echo(f"  Total number of files with errors: {total_files_with_errors:5}")
        if not errorsonly:
            click.echo(f"  Total number of warnings:          {total_warning_count:5}")
        click.echo(f"  Total number of errors:            {total_error_count:5}")
        click.echo("")

        file_counts = [
            (counts[0], counts[1], fn.split(os.sep)[-3], fn.split(os.sep)[-1])
            for (fn, counts) in files_to_errors.items()
        ]

        file_counts = list(reversed(sorted(file_counts)))
        printed_header = False
        for error_count, warning_count, locale, fn in file_counts:
            if not error_count and not warning_count:
                continue

            if not printed_header:
                if errorsonly:
                    click.echo("Errors  Filename")
                else:
                    click.echo("Warnings  Errors  Filename")
                printed_header = True

            if errorsonly:
                click.echo(f" {error_count:5}  {locale} ({fn})")
            else:
                click.echo(f"   {warning_count:5}   {error_count:5}  {locale} ({fn})")

    # Return 0 if everything was fine or 1 if there were errors.
    ctx.exit(code=1 if total_error_count else 0)


@cli.command()
@click.option(
    "--showuntranslated", is_flag=True, default=False, help="Show untranslated strings"
)
@click.option("--showfuzzy", is_flag=True, default=False, help="Show fuzzy strings")
@click.argument("path", nargs=-1, type=click.Path(exists=True))
@click.pass_context
def status(ctx, showuntranslated, showfuzzy, path):
    """Show status of a .po file."""
    click.echo(f"dennis version {__version__}")

    po_files = []
    for item in path:
        if os.path.isdir(item):
            for root, dirs, files in os.walk(item):
                po_files.extend(
                    [os.path.join(root, fn) for fn in files if fn.endswith(".po")]
                )
        else:
            po_files.append(item)

    po_files = [os.path.abspath(fn) for fn in po_files if fn.endswith(".po")]

    for fn in po_files:
        formatted_fn = click.format_filename(fn)
        try:
            if not os.path.exists(fn):
                raise IOError(f'File "{formatted_fn}" does not exist.')

            pofile = parse_pofile(fn)
        except IOError as ioe:
            err(f">>> Problem opening file: {formatted_fn}")
            err(repr(ioe))
            continue

        click.echo("")
        click.secho(f">>> Working on: {formatted_fn}", fg="green", bold=True)

        click.echo("Metadata:")
        for key in (
            "Language",
            "Report-Msgid-Bugs-To",
            "PO-Revision-Date",
            "Last-Translator",
            "Language-Team",
            "Plural-Forms",
        ):
            if key in pofile.metadata and pofile.metadata[key]:
                click.echo(f"  {key}: {pofile.metadata[key]}")
        click.echo("")

        if showuntranslated:
            click.echo("Untranslated strings:")
            click.echo("")
            for poentry in pofile.untranslated_entries():
                click.echo(withlines(poentry.linenum, poentry.original))
                click.echo("")

        if showfuzzy:
            click.echo("Fuzzy strings:")
            click.echo("")
            for poentry in pofile.fuzzy_entries():
                click.echo(withlines(poentry.linenum, poentry.original))
                click.echo("")

        total_words = 0
        translated_words = 0
        untranslated_words = 0
        for entry in pofile.translated_entries() + pofile.untranslated_entries():
            if not entry.translated():
                untranslated_words += len(entry.msgid.split())
            else:
                translated_words += len(entry.msgid.split())
            total_words += len(entry.msgid.split())

        total_strings = len(pofile)
        translated_total = len(pofile.translated_entries())
        fuzzy_total = len(pofile.fuzzy_entries())
        untranslated_total = len(pofile.untranslated_entries())

        click.echo("Statistics:")
        click.echo(f"  Total strings:             {total_strings}")
        click.echo(f"    Translated:              {translated_total}")
        click.echo(f"    Untranslated:            {untranslated_total}")
        click.echo(f"    Fuzzy:                   {fuzzy_total}")
        click.echo(f"  Total translateable words: {total_words}")
        click.echo(f"    Translated:              {translated_words}")
        click.echo(f"    Untranslated:            {untranslated_words}")
        if untranslated_words == 0:
            click.echo("  Percentage:                100% COMPLETE!")
        else:
            click.echo(f"  Percentage:                {pofile.percent_translated()}%")

    ctx.exit(0)


@cli.command()
@click.option(
    "--varformat",
    default="python-format,python-brace-format",
    help=("Comma-separated list of variable types. " "See Available Variable Formats."),
)
@click.option(
    "--pipeline",
    "-p",
    default="pirate",
    help=("Comma-separated translate pipeline. See Available " "Pipeline Parts."),
)
@click.option(
    "--strings",
    "-s",
    default=False,
    is_flag=True,
    help="Command line args are strings to be translated",
)
@click.argument("path", nargs=-1)
@click.pass_context
@epilog(format_formats() + "\n" + format_pipeline_parts())
def translate(ctx, varformat, pipeline, strings, path):
    """
    Translate a single string or .po file of strings.

    If you want to pull the string from stdin, use "-".

    Note: Translating files is done in-place replacing the original
    file.

    """
    if not (path and path[0] == "-"):
        # We don't want to print this if they're piping to stdin
        click.echo(f"dennis version {__version__}")

    if not path:
        raise click.UsageError("nothing to work on. Use --help for help.")

    try:
        translator = Translator(varformat.split(","), pipeline.split(","))
    except InvalidPipeline as ipe:
        raise click.UsageError(ipe.args[0])

    if strings:
        # Args are strings to be translated
        for arg in path:
            data = translator.translate_string(arg)
            click.echo(data)

    elif path[0] == "-":
        # Read everything from stdin, then translate it
        data = click.get_binary_stream("stdin").read()
        data = translator.translate_string(data)
        click.echo(data)

    else:
        # Check all the paths first
        for arg in path:
            if not os.path.exists(arg):
                raise click.UsageError(
                    "File {fn} does not exist.".format(fn=click.format_filename(arg))
                )

        for arg in path:
            click.echo(translator.translate_file(arg))

    ctx.exit(0)


def exception_handler(exc_type, exc_value, exc_tb):
    click.echo("Oh no! Dennis has thrown an error while trying to do stuff.")
    click.echo("Please write up a bug report with the specifics so that ")
    click.echo("we can fix it.")
    click.echo("")
    click.echo("https://github.com/willkg/dennis/issues")
    click.echo("")
    click.echo("Here is some information you can copy and paste into the ")
    click.echo("bug report:")
    click.echo("")
    click.echo("---")
    click.echo(f"Dennis: {__version__}")
    click.echo(f"Python: {sys.version}")
    click.echo(f"Command line: {sys.argv}")
    click.echo("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    click.echo("---")
