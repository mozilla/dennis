=======
Recipes
=======

.. contents::
   :local:


commit-msg git hook
===================

::

    #!/bin/bash

    (cat < $1 | dennis-cmd translate - | tail -n "+2" > $1.tmp) && mv $1.tmp $1

    # We always exit 0 in case dennis-cmd fails. Then you get your
    # original commit message. No one likes it when goofy shenanigans
    # break your stuff.
    exit 0;
