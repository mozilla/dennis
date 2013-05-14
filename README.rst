======
Read me
======

dennis is a command line utility for dealing with localization files.

It includes the following:

* **PIRATE!**

  Create a test locale by "translating" the strings in your messages.pot
  file into PIRATE! This translation has the following properties:

  1. every string has at least one unicode character in it
  2. every string is longer than the original msgid
  3. every string looks different than the original string, but
     it's still readable

* **locale linter**

  This "lints" a .po file looking for Python string formatting tokens
  and making sure that the tokens in the msgstr are the same as the
  ones in the msgid.


Why is it called dennis?
========================

This is how I name my software projects.


Install
=======

It's not on PyPI, yet. So this is how you install it for now.

::

    pip install https://github.com/willkg/dennis/archive/master.zip#egg=dennis


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
