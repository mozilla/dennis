========
Linting!
========

Help
====

::

    $ dennis-cmd lint --help


Summary
=======

dennis can lint your translated .po files for Python formatting token
issues::

    $ dennis-cmd lint messages.po


Produces output like this::

    (dennis) (M=3b9e7) saturn ~/mozilla/kitsune> dennis-cmd lint locale/it/
    LC_MESSAGES/messages.po
    dennis-cmd version 0.3.3
    >>> Working on: /home/willkg/mozilla/kitsune/locale/it/LC_MESSAGES/mess
    ages.po
    Error: mismatched: invalid variables: %(domain)s
    msgid: Did you know that %(answerer)s is a Firefox user just like you?
    Get started helping other Firefox users by <a href="https://%(host)s/qu
    estions?filter=unsolved"> browsing questions</a> -- you might just make
    someone's day!
    msgstr: Lo sai che %(answerer)s è un utente di Firefox proprio come te?
    Puoi aiutare anche tu gli altri utenti: <a href="https://%(domain)s/que
    stions?filter=unsolved">cerca tra le domande</a> e potrai fare felice u
    no di loro!

    Warning: mismatched: missing variables: %(host)s
    msgid: Did you know that %(answerer)s is a Firefox user just like you?
    Get started helping other Firefox users by <a href="https://%(host)s/qu
    estions?filter=unsolved"> browsing questions</a> -- you might just make
    someone's day!
    msgstr: Lo sai che %(answerer)s è un utente di Firefox proprio come te?
    Puoi aiutare anche tu gli altri utenti: <a href="https://%(domain)s/que
    stions?filter=unsolved">cerca tra le domande</a> e potrai fare felice u
    no di loro!

    Warning: mismatched: missing variables: {0}
    msgid: {0} question
    msgstr[0]: domanda

    Warning: mismatched: missing variables: {0}
    msgid: {0} question
    msgid_plural: {0} questions
    msgstr[1]: domande

    Warning: mismatched: missing variables: {0}
    msgid: {0} answer
    msgstr[0]: risposta

    Warning: mismatched: missing variables: {0}
    msgid: {0} answer
    msgid_plural: {0} answers
    msgstr[1]: risposte

    Warning: mismatched: missing variables: {0}
    msgid: {0} solution
    msgstr[0]: soluzione

    Warning: mismatched: missing variables: {0}
    msgid: {0} solution
    msgid_plural: {0} solutions
    msgstr[1]: soluzioni

    Error: mismatched: invalid variables: {group}
    msgid: Are you sure you want to remove {user} from the document contrib
    utors?
    msgstr: Rimuovere l'utente {user} dai collaboratori per il documento {g
    roup}?

    Totals
      Warnings:     7
      Errors:       2


This runs multiple lint rules on all the strings in the ``.po`` file
generating a list of errors and a list of warnings.

Wait, but that's ugly and hard to read! If you install ``blessings``, it
comes colorized and really easy to parse. All hail blessings!


Warnings
========

**What's a warning?**

It's an issue that probably indicates the translated string is
problematic, but it won't cause production code to die. For example,
when the original string has a Python variable the translated string
doesn't have. That's not great and probably means the translated
string needs to be updated, but it won't throw an error in production.


**List of warnings**

    **mismatched variable tokens**
        There are formatting variable tokens in the *original* string
        that aren't in the *translated* string.

        Example::

            Warning: mismatched: missing variables: {0}
            msgid: "{foo} bar"
            msgstr: "bar"



Errors
======

**What's an error?**

It's an issue that will throw an error in production and must be fixed
pronto. For example, when the translated string has a Python variable
that's not in the original string. When this string is interpolated,
it will kick up a Python error. That causes the software to die, users
to be unhappy, tires to go flat, people to work on weekends, mass
hysteria, etc. No one likes that. I don't like that. You probably
don't like that, either.


**List of errors**

    **mismatched variable tokens**
        There are formatting variable tokens in the *translated* string
        that aren't in the original string.

        Example::

            Error: mismatched: invalid variables: {foo}
            msgid: "bar"
            msgstr: "{foo} bar"

    **malformed**
        The variable in the translated string is malformed or there are
        characters in the translated string that will cause it to be
        parsed as if it had variables.

        Example (Python)::

            Error: malformed variables: {foo bar baz
            msgid: "{foo} bar baz"
            msgstr: "{foo bar baz"

        Example (Python)::

            Error: malformed variables: %(count)
            msgid: "%(count)s view"
            msgstr: "%(count) view"
