=======
Recipes
=======

.. contents::
   :local:


linting all your .po files
==========================

Sometimes it's good to just get a look at all the .po files and make
sure they're ok::

    dennis-cmd lint locale/


It'll give you a summary at the end.


translate .po file for l10n issue detection
===========================================

Use the Dennis translator to find l10n issues in your application
without having to bother your translators.

For example, this translates strings into Pirate for a web application
written in Python::

    #!/bin/bash

    mkdir -p locale/xx/LC_MESSAGES
    cp locale/templates/LC_MESSAGES/messages.pot \
        locale/xx/LC_MESSAGES/messages.po

    dennis-cmd translate --pipeline=html,pirate --types=python \
        locale/xx/LC_MESSAGES/messages.po


Now view your application with the ``xx`` locale and behold it's
Piratey wonderfulness!


selective .mo compiling
=======================

The Dennis linter returns an exit code of 1 if the file(s) it's
linting have errors. You can trivially use this to selectively compile
.po files into .mo files iff they are error free::

    #!/bin/bash

    for pofile in `find locale/ -name "*.po"`
    do
        dir=`dirname "$pofile"`
        stem=`basename "$pofile" .po`

        dennis-cmd lint --errorsonly "$pofile"
        if [ $? -ne 0 ]
        then
            echo "ERRORZ!!! Not compiling $pofile!"

        else
            msgfmt -o "${dir}/${stem}.mo" "$pofile"
        fi
    done


commit-msg git hook
===================

You can automatically translate all future commit messages for your
git project by creating a ``commit-msg`` hook like this::

    #!/bin/bash

    # Pipe the contents of the commit message file through dennis to
    # a temp file, then copy it back.
    (cat < $1 | dennis-cmd translate - > $1.tmp) && mv $1.tmp $1

    # We always exit 0 even if the dennis-cmd fails. If the dennis-cmd
    # fails, you get your original commit message. No one likes it when
    # shenanigans break your stuff for realz.
    exit 0;


convert your web page into Pirate for April fools day
=====================================================

The Dennis translator can take content from stdin. Translate entire
HTML pages::

    #!/bin/bash

    (cat < "$1" | dennis-cmd translate --pipeline=html,pirate -) > "pirate_$1"


Or show how you really feel about April fools day on the Internet::

    #!/bin/bash

    (cat < "$1" | dennis-cmd translate --pipeline=html,haha -) > "haha_$1"
