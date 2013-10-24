=======
Read me
=======

dennis is a command line tool for translating and linting .po files.

It includes the following subcommands:

* **lint**: Lints ``.po`` files for problems including errors that
  can cause your production system to crash.

  The system allows for defining other variable formats.

* **status**: Get a high-level status of a ``.po`` file including
  a list of unstranslated strings.

* **translate**: Translates strings in ``.po`` files into something
  else! Comes with an HTML extractor (tokenizes strings so that only
  the text is translated) and a bunch of translations like
  Pirate!. This is helpful for l10n testing, development, finding
  unicode/layout problems, amazing your friends, hilarious April 1st
  shenanigans, etc.

  The system allows for other translators and extractors using a
  loosely coupled pipeline.

  This also works on strings passed in as command line arguments and
  as stdin---it doesn't have to be a ``.po`` file or in a ``.po``
  format. Dennis uses dennis to translate all dennis commit messages
  into Pirate!. That's how cool dennis is!


Quick start
===========

Install::

    $ pip install dennis
    $ pip install blessings  # Optional for prettier output

Lint a ``.po`` file for problems::

    $ dennis-cmd lint locale/fr/LC_MESSAGES/messages.po

Lint all your ``.po`` files for errors::

    $ dennis-cmd lint --errorsonly locale/

Translate a ``.po`` file in place into Pirate!::

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


Why is it called dennis?
========================

This is how I name my software projects.
