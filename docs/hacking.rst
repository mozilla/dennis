.. _hacking-chapter:

=================
Hacking on Dennis
=================

This covers setting up Dennis to hack on. If you're interested in
using Dennis, but not hacking on it, then this probably isn't going to
be interesting to you.


Install Dennis and dependencies for development
===============================================

1. Clone the repository from https://github.com/mozilla/dennis/
2. Create a virtual environment
3. Install dev requirements: ``pip install -r requirements-dev.txt``

This should get you up and running.


Helping out
===========

The non-exhaustive list of things to do are in the `issue tracker
<https://github.com/mozilla/dennis/issues>`_.

If you want to write some code or fix a bug or add some docs or in
some way contribute to Dennis, please do so using the following
process:

1. Tell me what you're planning to do before you do it. Preferably in
   a comment in the issue tracker on a relevant issue. If not as a
   comment, then email me.

   After I've been informed and given approval, continue!

2. Create a new branch for your changes.

3. Make your changes!

4. Update documentation or write new documentation for the changes
   you've made.

5. Update the tests or write new tests for the changes you've made.

6. Submit a patch.

   To make it easier for me to maintain Dennis, all changes should
   either:

   1. be submitted as a pull request in Github, or

   2. emailed to me as an appropriately formatted patch

   If you don't know how to do either, then maybe you can find someone
   to help you out.


That's it!

Anyone who contributes code, tests or docs (in other words, has a git
commit with their name on it) get added to the CONTRIBUTORS file. Yay!


Tests
=====

Tests are in ``tests/``. We use pytest as the test
runner.

To run the tests, do::

    $ pytest

Please write tests for changes you make.


Documentation
=============

Documentation is in ``docs/``. We use `Sphinx
<https://sphinx-doc.org/>`_ as the documentation generator.

To build the docs, do::

    $ cd docs/
    $ make html

Please make changes to the documentation as required by the changes
you make.


Release howto
=============

1. Check out master tip.

2. Check to make sure ``setup.py`` and ``requirements-dev.txt`` files have
   correct versions of requirements.

3. Update version number in ``dennis/__init__.py``

   1. Set ``__version__`` to something like ``0.4``.
   2. Set ``__releasedate__`` to something like ``20120731``.

4. Update ``CHANGELOG``. Usually, I do something like::

       git log --oneline v0.4..HEAD

   replacing ``v0.4`` with the most recent tag. Then I copy and paste that,
   remove uninteresting lines and add a header.

5. Verify correctness.

   1. Run the tests with ``tox``.
   2. Review the ``README.rst``.
   3. Build the docs and review them.

6. Tag the release::

       git tag -a v0.4

   Copy the last section of the ``CHANGELOG`` into the tag commit message.

7. Push everything::

       git push --tags official master

8. Update PyPI::

       rm -rf dist/*
       python setup.py sdist bdist_wheel
       twine upload dist/*

9. Announce the release.
