=======
Recipes
=======

.. contents::
   :local:


commit-msg git hook
===================

You can automatically translate all future commit messages for your
git project by creating a ``commit-msg`` hook like this::

    #!/bin/bash

    # Pipe the contents of the commit message file through dennis,
    # then knock off the first line (it's the dennis version number)
    # and copy it back.
    (cat < $1 | dennis-cmd translate - | tail -n "+2" > $1.tmp) && mv $1.tmp $1

    # We always exit 0 even if the dennis-cmd fails. If the dennis-cmd
    # fails, you get your original commit message. No one likes it when
    # shenanigans break your stuff for realz.
    exit 0;
