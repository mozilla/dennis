============
Translating!
============

dennis can translate the strings in your ``.po`` file. For example,
this does the default which extracts text from HTML strings and
translates that text into Pirate::

    $ dennis-cmd translate messages.po


.. Note::

   This translates the ``messages.po`` file in-place. If you don't
   want that, then copy it and translate the copy.


You can also translate strings on the command line::

    $ dennis-cmd translate -s "Dennis is my friend"


You can translate stuff from stdin::

    $ echo "Dennis can see the future" | dennis-cmd translate -


You can change the pipeline to use one of many exciting
transforms. For example, this is extra-piraty and shouty!::

    $ dennis-cmd translate --pipeline=pirate,pirate,shouty \
        -s "Dennis can make hard boiled eggs boil faster"


Dennis can translate around variable tokens in strings. By default, it
translates around Python variable forms. You can specify other types
to translate around::

    $ denis-cmd translate --types=python


.. Note::

   The infrastructure is there for handling other types, but it
   doesn't actually support other variable types, yet. Help me add
   additional formats that are used in gettext strings!


For help and a list of types and transforms, do this::

    $ dennis-cmd translate


For more about pipelines, see :ref:`translating-chapter-pipelines`.

For more about other transforms, see
:ref:`translating-chapter-transforms`.

For more about extending Dennis to do dirty things, see
:ref:`api-chapter`.

.. _translating-chapter-transforms:

Transforms
==========

Dennis currently supports the following transforms:

==========  ================================================
name        description
==========  ================================================
anglequote  Encloses string in unicode angle quotes.
empty       Returns empty strings.
haha        Adds haha! before sentences in a string.
pirate      Translates text into Pirate!
redacted    Redacts everything.
shouty      Translates into all caps.
xxx         Adds xxx before and after lines in a string.
==========  ================================================

Aditionally, there's the html transform which extracts the bits to be
translated, but doesn't do any translation itself:

==========  ================================================
name        description
==========  ================================================
html        Tokenizes HTML bits so only text is translated.
==========  ================================================


anglequote
----------

The anglequote transform adds unicode angle quotes to the beginning
and end of strings. This helps to make sure your code handles unicode
strings and also some layout issues like when strings are cut off or
overlapping.


empty
-----

The empty transform nixes the string.

OMG! Why?!

This is helpful for building .pot files from .po files. Also, it's
sort of interesting to see a ui with no text in it.


haha
----

Haha❗ Adds "Haha!" before sentences in a string. Haha❗ The exclamation
point is a non-ASCII character, so this is both fun and tests unicode
handling!


pirate
------

The Pirate! translation has the following properties:

1. it's longer than the English equivalent (tests layout issues)
2. it's different than the English equivalent (tests missing gettext calls)
3. every string ends up with a non-ascii character (tests unicode handling)
4. looks close enough to the English equivalent that you can quickly
   figure out what's wrong (doesn't test your reading comprehension)


redacted
--------

Xxx xxxxxxxx xxxxxxxxx xxxxxxx xxxxxxxxxx.


shouty
------

THE SHOUTY TRANSFORM MAKES THINGS IN ALL ASCII UPPERCASE. SHOUTY
SHOUTY SHOUTY.


xxx
---

The xxx transform wraps all lines in strings with xxx.


html
----

The html transform extracts strings from HTML to be translated. This
includes any TEXT nodes as well as the text in alt and title
attributes.


.. _translating-chapter-pipelines:

Pipelines
=========

A pipeline consists of one or more transforms connected together. The
output of one transform is the input of the next transform.

Each transform takes an iterable of Tokens and outputs an iterable of
Tokens. In this way, you can build your pipeline however you like. For
more on this and how to build your own transforms, see
:ref:`api-chapter`.

Sample string: "<b>Dennis can make your dreams come true.</b>"

Example pipelines:

* ``pirate``

  Translates into Pirate!

  Sample string::

      <b>Dennis can make yerr dreams come true.</b> ye scalleywag❗

  Note that this isn't extracting HTML, so it just considers that
  whole thing a single string.

* ``shouty,pirate``

  Capitalizes everything in the string (including the html) then runs
  that through pirate.

  Sample string::

      <B>DENNIS CAN MAKE YOUR DREAMS COME TRUE.</B> ye scalleywag❗

  Note that this isn't extracting HTML, so it just considers that
  whole thing a single string.

* ``html,pirate,pirate,pirate,shouty``

  Extracts text from HTML to be translated, runs it through pirate
  multiple times, then runs it through shouty which results in an
  extra Piraty shouty string

  Sample string::

      <b>DENNIS CAN MAKE YARRRRR DREAMS COME TRUE PREPARE TO BE BOARD'D❗
      YE LANDLUBBARRS❗ MATEY❗.</b>

* ``empty,anglequote``

  Woah---where'd the words go? It's like a ghost-town of a ui.

  Sample string::

      «»
