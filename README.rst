======
Read me
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

* **lint**: Lints ``.po`` files for cases where there are variable
  formatting tokens in msg strings that aren't in the translated
  strings and vice versa.

  The system allows for defining other variable formats.


Why is it called dennis?
========================

This is how I name my software projects.


Install
=======

It's not on PyPI, yet. So this is how you install it for now.

::

    pip install https://github.com/willkg/dennis/archive/master.zip#egg=dennis


(Optional) Install `blessings
<https://pypi.python.org/pypi/blessings/>`_ if you want fancy
color-coded output. You want fancy color-coded output.

::

    pip install blessings


Basic usage until I write real docs
===================================

For more details, do::

    $ dennis-cmd

The subcommands also have help.


Linting!
--------

dennis can lint your translated .po files for Python formatting token
issues::

    $ dennis-cmd lint messages.po

Produces output like this::

    (dennis) 1 (M=dcfdd scripts/) saturn ~/mozilla/kitsune> dennis-cmd lint
    locale/it/LC_MESSAGES/messages.po
    dennis-cmd version 0.1.dev
    >>> Working on: /home/willkg/mozilla/kitsune/locale/it/LC_MESSAGES/mess
    ages.po
    Error: invalid tokens: %(domain)s
    Warning: missing tokens: %(host)s
    msgid: "Did you know that %(answerer)s is a Firefox user just like you?
    Get started helping other Firefox users by <a href="https://%(host)s/qu
    estions?filter=unsolved"> browsing questions</a> -- you might just make
    someone's day!"
    msgstr: "Lo sai che %(answerer)s è un utente di Firefox proprio come te
    ? Puoi aiutare anche tu gli altri utenti: <a href="https://%(domain)s/q
    uestions?filter=unsolved">cerca tra le domande</a> e potrai fare felice
    uno di loro!"

    Warning: missing tokens: {0}
    msgid: "{0} question"
    msgid_plural: "{0} question"
    msgstr[0]: "domanda"

    Warning: missing tokens: {0}
    msgid: "{0} question"
    msgid_plural: "{0} questions"
    msgstr[1]: "domande"

    Warning: missing tokens: {0}
    msgid: "{0} answer"
    msgid_plural: "{0} answer"
    msgstr[0]: "risposta"

    Warning: missing tokens: {0}
    msgid: "{0} answer"
    msgid_plural: "{0} answers"
    msgstr[1]: "risposte"

    Warning: missing tokens: {0}
    msgid: "{0} solution"
    msgid_plural: "{0} solution"
    msgstr[0]: "soluzione"

    Warning: missing tokens: {0}
    msgid: "{0} solution"
    msgid_plural: "{0} solutions"
    msgstr[1]: "soluzioni"

    Error: invalid tokens: {group}
    msgid: "Are you sure you want to remove {user} from the document contri
    butors?"
    msgstr: "Rimuovere l'utente {user} dai collaboratori per il documento {
    group}?"

    Total:  2063  Warnings:     7  Errors:     2

What's a warning? It's when the original string has a variable the
translated string doesn't have. That's not great---probably means the
translated string is wrong. It probably won't kick up an error causing
your software to fail.

What's an error? It's when the translated string has a variable that's
not in the original string. When you go to interpolate this in Python,
it kicks up an error. That causes software to die, users to be
unhappy, tires to go flat, people to work on weekends, mass hysteria,
etc. No one likes that. I don't like that.


Translating!
------------

dennis can translate the strings in your ``.po`` file. For example,
this does the default which extracts text from HTML strings and
translates that text into Pirate::

    $ dennis-cmd translate messages.po


This translates the file in-place. If you don't want that, then copy
it and translate the copy.

The Pirate! translation has the following properties:

1. it's longer than the English equivalent (tests layout issues)
2. it's different than the English equivalent (tests missing gettext calls)
3. every string ends up with a non-ascii character (tests unicode handling)
4. looks close enough to the English equivalent that you can quickly
   figure out what's wrong (doesn't test your reading comprehension)

Don't like Pirate!? Are your strings not HTML? Then you can specify a
pipeline with other transforms.


Status
======

July 8th, 2013

I overhauled a lot of code, added tests and fiddled with some
things. It's good enough for my uses now.

If it's not good enough for yours, please add an issue to the
tracker. If it's something I'm interested in, I might work on
it. Probably not, though.

If you're interested in working on things, let me know first
preferably by opening up an issue and commenting in it.


Project details
===============

:Code:          http://github.com/willkg/dennis
:Documentation: http://dennis.rtfd.org/ (not yet)
:Issue tracker: https://github.com/willkg/dennis/issues
:License:       BSD 3-clause; see LICENSE file
