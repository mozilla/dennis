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


Project details
===============

:Code:          http://github.com/willkg/dennis
:Documentation: http://dennis.rtfd.org/ (not yet)
:Issue tracker: https://github.com/willkg/dennis/issues
:License:       BSD 3-clause; see LICENSE file
