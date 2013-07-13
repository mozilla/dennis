========
Linting!
========

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
