========
Linting!
========

Help
====

::

    $ dennis-cmd lint --help

This will list the available lint rules and codes, the variable
formats and any additional options available.


Summary
=======

Dennis can lint your translated PO files for Python formatting
token issues::

    $ dennis-cmd lint messages.po


This runs multiple lint rules on all the strings in the PO file
generating a list of errors and a list of warnings.

Wait, but that's ugly and hard to read! If you install ``blessings``, it
comes colorized and really easy to parse. All hail blessings!

Dennis can also lint your POT files and point out issues that can
result in poor translations. You can lint POT files like this::

    $ dennis-cmd lint messages.pot


Skipping rules string-by-string
===============================

In the extracted comment, you can tell Dennis to ignore lint rules (or
all lint rules).

Ignore everything::

    #. dennis-ignore: *
    msgid "German makes up 10% of our visitor base"
    msgstr "A német a látogatóbázisunk 10%-át teszi ki"

Ignore specific rules (comma-separated)::

    #. dennis-ignore: E101,E102,E103
    msgid "German makes up 10% of our visitor base"
    msgstr "A német a látogatóbázisunk 10%-át teszi ki"

Ignore everything, but note the beginning of the line is ignored by
Dennis so you can tell localizers to ignore the ignore thing::

    #. localizers--ignore this comment. dennis-ignore: *
    msgid "German makes up 10% of our visitor base"
    msgstr "A német a látogatóbázisunk 10%-át teszi ki"


Warnings and Errors
===================

What's a warning?
-----------------

Warnings indicate the translated string is either outdated or a poor
translation, but the string is fine in the sense that it won't kick
up an error in production.

For example, say the original string has a variable, but the
translated string doesn't use that variable.

That's not great and probably means the translated string needs to be
updated, but it won't throw an error in production.


What's an error?
----------------

Errors indicate problems with the translated string that will cause
an error to be thrown. These should get fixed pronto.

For example, when the translated string has a Python variable that's
not in the original string. When this string is interpolated, it will
kick up a Python error. That causes the software to die, users to be
unhappy, tires to go flat, people to work on weekends, mass hysteria,
etc. No one likes that. I don't like that. You probably don't like
that, either.


Table of Warnings and errors
============================

PO files
--------

+------+-----------------------------------------------------------------------+
| Code | Description                                                           |
+======+=======================================================================+
| E101 | Malformed variable missing type                                       |
|      |                                                                       |
|      | Only checks pythonpercent variables.                                  |
|      |                                                                       |
|      | Example (Python)::                                                    |
|      |                                                                       |
|      |     Error: malformed variables: %(count)                              |
|      |     msgid: "%(count)s view"                                           |
|      |     msgstr: "%(count) view"                                           |
|      |                                                                       |
|      | >>> "%(count) view" % {"count": 5}                                    |
|      | Traceback (most recent call last):                                    |
|      |   File "<stdin>", line 1, in <module>                                 |
|      | ValueError: unsupported format character 'v' (0x76) at index 9        |
|      | >>>                                                                   |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| E102 | Malformed variable missing right curly-brace                          |
|      |                                                                       |
|      | For example ``{foo`` with missing ``}``.                              |
|      |                                                                       |
|      | Only checks pythonformat variables.                                   |
|      |                                                                       |
|      | Example (Python)::                                                    |
|      |                                                                       |
|      |     Error: malformed variables: {foo bar baz                          |
|      |     msgid: "{foo} bar baz"                                            |
|      |     msgstr: "{foo bar baz"                                            |
|      |                                                                       |
|      | >>> "{foo bar baz".format(foo="some thing")                           |
|      | Traceback (most recent call last):                                    |
|      |   File "<stdin>", line 1, in <module>                                 |
|      | ValueError: unmatched '{' in format                                   |
|      | >>>                                                                   |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| E103 | Malformed variable missing left curly-brace                           |
|      |                                                                       |
|      | For example ``foo}`` with missing ``{``.                              |
|      |                                                                       |
|      | Only checks pythonformat variables.                                   |
|      |                                                                       |
|      | Example (Python)::                                                    |
|      |                                                                       |
|      |     Error: malformed variables: foo}                                  |
|      |     msgid: "{foo} bar baz"                                            |
|      |     msgstr: "foo} bar baz"                                            |
|      |                                                                       |
|      | >>> "foo}".format(foo="some thing")                                   |
|      | Traceback (most recent call last):                                    |
|      |   File "<stdin>", line 1, in <module>                                 |
|      | ValueError: Single '}' encountered in format string                   |
|      | >>>                                                                   |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| E201 | Invalid variables in translated string                                |
|      |                                                                       |
|      | There are formatting variable tokens in the *translated* string       |
|      | that aren't in the original string.                                   |
|      |                                                                       |
|      | Example::                                                             |
|      |                                                                       |
|      |     Error: mismatched: invalid variables: {helpurl}                   |
|      |     msgid: "You can find help at {url}"                               |
|      |     msgstr: "You can find help at {helpurl}"                          |
|      |                                                                       |
|      | In this example, "helpurl" won't be in the list of variables to       |
|      | interpolate and this will throw a KeyError. That's equivalent         |
|      | to this:                                                              |
|      |                                                                       |
|      | >>> "You can find help at {helpurl}".format(url="http://example.com") |
|      | Traceback (most recent call last):                                    |
|      |   File "<stdin>", line 1, in <module>                                 |
|      | KeyError: 'helpurl'                                                   |
|      | >>>                                                                   |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| W202 | Missing variables in translated string                                |
|      |                                                                       |
|      | There are formatting variable tokens in the *original* string         |
|      | that aren't in the *translated* string.                               |
|      |                                                                       |
|      | Example::                                                             |
|      |                                                                       |
|      |     Warning: mismatched: missing variables: {url}                     |
|      |     msgid: "You can find help at {url}"                               |
|      |     msgstr: "Get help!"                                               |
|      |                                                                       |
+------+-----------------------------------------------------------------------+
| W301 | String is all whitespace                                              |
|      |                                                                       |
|      | The translated string is all whitespace.                              |
|      |                                                                       |
|      | Example::                                                             |
|      |                                                                       |
|      |    Error: blank: translated string is solely whitespace               |
|      |    msgid: "Foo"                                                       |
|      |    msgstr: "  "                                                       |
|      |                                                                       |
+------+-----------------------------------------------------------------------+


POT files
---------

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
