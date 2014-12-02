=======
Read me
=======

Dennis is a command line tool for translating and linting .po files.

It includes the following subcommands:

* **lint**: Lints ``.po`` files for problems including errors that
  can cause your production system to crash.

  The system allows for defining other variable formats.

* **linttemplate**: Lints ``.pot`` files for problems in strings that
  lead to poor localizations.

* **status**: Get a high-level status of a ``.po`` file including
  a list of unstranslated strings.

* **translate**: Translates strings in ``.po`` files into something
  else! Comes with an HTML extractor (tokenizes strings so that only
  the text is translated) and a bunch of translations like
  Pirate!.

  This is helpful for l10n testing, development, finding unicode/layout
  problems, amazing your friends, hilarious April 1st shenanigans, etc.

  Specify the tokenizer/transform pipeline you want to use that combines
  things. Zombie? Sure! Shouty Zombie? Ok! Manic shouty Dubstep? Bring
  it on!

  This also works on strings passed in as command line arguments and
  as stdin---it doesn't have to be a ``.po`` file or in a ``.po``
  format. For example, Dennis uses Dennis to translate all Dennis
  commit messages into Pirate!. That's how cool Dennis is!


Quick start
===========

Install::

    $ pip install dennis
    $ pip install blessings  # Optional for prettier lint output

Lint a ``.po`` file for problems::

    $ dennis-cmd lint locale/fr/LC_MESSAGES/messages.po

Lint all your ``.po`` files for errors::

    $ dennis-cmd lint --errorsonly locale/

Lint a ``.pot`` file for problems::

    $ dennis-cmd linttemplate locale/templates/LC_MESSAGES/messages.pot

Translate a ``.po`` file with HTML in the strings in place into Pirate!::

    $ dennis-cmd translate --pipeline=html,pirate \
        locale/xx/LC_MESSAGES/messages.po

Get help::

    $ dennis-cmd


Project details
===============

:Code:          http://github.com/willkg/dennis
:Documentation: http://dennis.rtfd.org/
:Issue tracker: https://github.com/willkg/dennis/issues
:License:       BSD 3-clause; see LICENSE file
:Donate:        `gittip <https://www.gittip.com/on/github/willkg/>`_


Why is it called Dennis?
========================

This is how I name my software projects.
