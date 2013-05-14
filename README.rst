======
Read me
======

dennis is a command line tool for translating and linting .po files.

It includes the following subcommands:

* **translate**: Translates .po files into Pirate! which is helpful
  for l10n testing, development, finding unicode/layout issues, etc.
* **lint**: Lints .po files making sure Python formatting tokens are
  correct in translated files.


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
color-coded output.

::

    pip install blessings


Basic usage until I write real docs
===================================

Linting!
--------

dennis can lint your translated .po files for Python formatting token issues::

    $ dennis-cmd lint messages.po

Produces output like this::

    saturn ~/mozilla/kitsune/locale/fr/LC_MESSAGES> dennis-cmd lint messages.po
    dennis-cmd version 0.1.dev
    Working on /home/willkg/mozilla/kitsune/locale/fr/LC_MESSAGES/messages.po

    Warning: missing tokens: {url}
    Error: invalid tokens: %(aaq_url)s
    msgid: "You don't need to register to <a href="{url}">ask a question</a>."
    msgstr: "Vous n'avez pas besoin de vous inscrire pour <a href="%(aaq_url)s">poser une question</a>."

    Warning: missing tokens: {locale}
    msgid: "Category in {locale}:"
    msgstr: "Catégories :"

    Warning: missing tokens: {format}, {type}
    msgid: "Delete this video {type} ({format})"
    msgstr: "Supprimer ce type"

    Warning: missing tokens: {format}, {type}
    msgid: "Delete this {type} ({format})"
    msgstr: "Supprimer ce type"

    Verified 1965 messages in messages.po. 1 errors.


Translating!
------------

dennis can translate your .po file into Pirate!::

    $ dennis-cmd translate messages.po

This translates the file in-place. The translated strings have the
following properties:

1. it's longer than the English equivalent (tests layout issues)
2. it's different than the English equivalent (tests missing gettext calls)
3. every string ends up with a non-ascii character (tests unicode handling)
4. looks close enough to the English equivalent that you can quickly
   figure out what's wrong (doesn't test your reading comprehension)


Status
======

May 14th, 2013

I wrote some of this code years ago and some recently. This pulls it
all together into a tools package others can use. There are similar
tools out there, but when I looked at them I wasn't excited and/or
they didn't meet my specific needs.

This needs a few more hours to gel into something releasable.


Project details
===============

:Code:          http://github.com/willkg/dennis
:Documentation: http://dennis.rtfd.org/ (not yet)
:Issue tracker: https://github.com/willkg/dennis/issues
:License:       BSD 3-clause; see LICENSE file
