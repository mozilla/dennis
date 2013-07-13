======
Dennis
======

dennis is a command line tool for translating and linting .po files.

It includes the following subcommands:

* **translate**: Translates strings in ``.po`` files into something
  else!  Comes with an HTML extractor (tokenizes strings so that only
  the text is translated) and a Pirate! translation. This is helpful
  for l10n testing, development, finding unicode/layout problems,
  amazing your friends, hilarious April 1st shenanigans, etc.

  The system allows for other translators and extractors using a
  loosely coupled pipeline.

  This also works on strings passed in as command line arguments and
  as stdin---it doesn't have to be a ``.po`` file or in a ``.po``
  format.

* **lint**: Lints ``.po`` files for cases where there are variable
  formatting tokens in msg strings that aren't in the translated
  strings and vice versa.

  The system allows for defining other variable formats.


Quick start
===========

Install::

    $ pip install dennis
    $ pip install blessings  # Optional for pretty output

Lint::

    $ dennis-cmd lint locale/fr/LC_MESSAGES/messages.po

Translate::

    $ dennis-cmd translate --pipeline=html,pirate \
        locale/xx/LC_MESSAGES/messages.po

Get help::

    $ dennis-cmd


Project details
===============

:Code:          http://github.com/willkg/dennis
:Documentation: http://dennis.rtfd.org/ (not yet)
:Issue tracker: https://github.com/willkg/dennis/issues
:License:       BSD 3-clause; see LICENSE file


User guide
==========

.. toctree::
   :maxdepth: 2

   changelog
   translating
   linting
   api
   recipes


Project guide
=============

.. toctree::
   :maxdepth: 2

   hacking
   license
   contributors


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
