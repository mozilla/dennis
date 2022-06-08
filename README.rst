=======
Read me
=======

Dennis is a set of utilities for working with PO files to ease
development and improve quality. Translate POT files to find problems
with localization in your code. Lint PO files for common problems like
variable formatting, mismatched HTML, missing variables, etc.

It includes the following subcommands:

* **lint**: Lints PO and POT files for problems including errors that
  can cause your production system to crash and problems in strings that
  can lead to poor translations.

  The system allows for defining other variable formats.

* **status**: Get a high-level status of a PO file including a list of
  unstranslated strings.

* **translate**: Translates strings in PO files into something else!
  Comes with an HTML extractor (tokenizes strings so that only the text
  is translated) and a bunch of translations like Pirate!.

  This is helpful for l10n testing, development, finding unicode/layout
  problems, amazing your friends, hilarious April 1st shenanigans, etc.

  Specify the tokenizer/transform pipeline you want to use that combines
  things. Zombie? Sure! Shouty Zombie? Ok! Manic shouty Dubstep? Bring
  it on!

  This also works on strings passed in as command line arguments and
  as stdin---it doesn't have to be a PO file or in a PO format
  format. For example, Dennis uses Dennis to translate all Dennis
  commit messages into Pirate!. That's how cool Dennis is!


Quick start
===========

Install::

    $ pip install dennis

Lint a PO file for problems::

    $ dennis-cmd lint locale/fr/LC_MESSAGES/messages.po

Lint all your PO files for errors::

    $ dennis-cmd lint --errorsonly locale/

Lint a POT file for problems::

    $ dennis-cmd lint locale/templates/LC_MESSAGES/messages.pot

Translate a PO file in place into Pirate!::

    $ dennis-cmd translate --pipeline=html,pirate \
        locale/xx/LC_MESSAGES/messages.po

Get help::

    $ dennis-cmd


Project details
===============

:Code:          https://github.com/willkg/dennis
:Documentation: https://dennis.readthedocs.io/
:Issue tracker: https://github.com/willkg/dennis/issues
:License:       BSD 3-clause; see LICENSE file


Why is it called Dennis?
========================

This is how I name my software projects.
