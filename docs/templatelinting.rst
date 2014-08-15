=================
Template Linting!
=================

Help
====

::

    $ dennis-cmd linttemplate --help

This will list the available lint rules and codes, the variable
formats and any additional options available.


Summary
=======

dennis can lint your template files for various issues that are common causes
for translation problems.

Example usage::

    $ dennis-cmd linttemplate messages.pot

This runs all available template lint rules on all the strings in the ``.pot``
file and prints out warnings.


Skipping rules string-by-string
===============================

In the extracted comment, you can tell dennis to ignore individual template
lint rules (or all template lint rules).

Ignore everything::

    #. dennis-ignore: *
    msgid "Title: {t}"
    msgstr ""

Ignore specific rules (comma-separated)::

    #. dennis-ignore: W501
    msgid "Title: {t}"
    msgstr ""

Ignore everything, but note the beginning of the line is ignored by
dennis so you can tell localizers to ignore the ignore thing::

    #. localizers--ignore this comment. dennis-ignore: *
    msgid "Title: {t}"
    msgstr ""


Warnings
========

What's a warning?
-----------------

The template linter only issues warnings. A warning indicates that the
template linter sees something that could be a common cause for
translation problems.

For example, say the string has a variable ``l``. That's a hard-to-read
variable and is often confused with ``1``. Further, the letter l
doesn't give any indication to the translator what kind of thing goes
in that variable. This can cause a variety of translation problems.


Table of Warnings
-----------------

+------+-----------------------------------------------------------------------+
| Code | Description                                                           |
+======+=======================================================================+
| W500 | Hard to read variable name                                            |
|      |                                                                       |
|      | There are a series of letters and numbers which are hard to           |
|      | distinguish from one another: o, O, 0, l, 1. It's not uncommon        |
|      | for a hard-working translator to misread and use the wrong character. |
|      |                                                                       |
|      | Example::                                                             |
|      |                                                                       |
|      |     Warning: hardtoread: hard to read variable name "l"               |
|      |     msgid: "Title: {l}"d help at {url}"                               |
|      |     msgstr: ""                                                        |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| W501 | One character variable name                                           |
|      |                                                                       |
|      | Using a one character variable name doesn't give enough context to    |
|      | the translator about what's being put in that variable.               |
|      |                                                                       |
|      | Example::                                                             |
|      |                                                                       |
|      |     Warning: onechar: one character variable name: "{t}"              |
|      |     msgid: "{t} | {c}"                                                |
|      |     msgstr: ""                                                        |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| W502 | Multiple unnamed variables                                            |
|      |                                                                       |
|      | Having one unnamed variable is ok since it's not order-dependent.     |
|      | However, having more than one unnamed variable means those variabes   |
|      | must occur in an order specified outside of the string. This creates  |
|      | problems with RTL languages and any other language that might need to |
|      | change the order of the variables to create a translation that makes  |
|      | sense.                                                                |
|      |                                                                       |
|      | Example::                                                             |
|      |                                                                       |
|      |    Warning: multiple variables with no name                           |
|      |    msgid: "%s replies to %s"                                          |
|      |    msgstr: ""                                                         |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
