==========
Statusing!
==========

Help
====

::

    $ dennis-cmd status --help


Summary
=======

Sometimes you just want to see the high-level status of a PO file and
also maybe see the list of untranslated strings.

You can do that with Dennis::

    $ dennis-cmd status messages.po


This will spit out riveting PO metadata and strings statistics like
the total number of translated strings, untranslated strings, fuzzy
strings and percentage translated.

Additionally, you can tell Dennis to show you all the untranslated
strings::

    $ dennis-cmd status --showuntranslated messages.po


Now you can verify that translation has been completed on a PO file
without reading through the PO file.
