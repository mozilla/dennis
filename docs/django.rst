========================
Using Dennis with Django
========================

Dennis has some shims to make it easier to use with a Django project.

To use Dennis with Django add ``dennis.django_dennis`` to ``INSTALLED_APPS``.

After you do that, then ``lint`` and ``translate`` subcommands are
available in``manage.py``::

    $ ./manage.py lint
    $ ./manage.py translate
