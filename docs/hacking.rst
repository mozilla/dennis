.. _hacking-chapter:

=================
Hacking on Dennis
=================

This covers setting up Dennis to hack on. If you're interested in
using Dennis, but not hacking on it, then this probably isn't going to
be interesting to you.


Install Dennis and dependencies for development
===============================================

1. Clone the repository from https://github.com/willkg/dennis/
2. Create a virtual environment
3. Run: ``python setup.py develop``
4. Install some other bits: ``pip install -r requirements-dev.txt``


This should get you up and running.


Helping out
===========

The non-exhaustive list of things to do are in the `issue tracker
<https://github.com/willkg/dennis/issues>`_.

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

Tests are in ``tests/``. We use py.test as the test
runner.

To run the tests, do::

    $ py.test

Please write tests for changes you make.


Documentation
=============

Documentation is in ``docs/``. We use `Sphinx
<http://sphinx-doc.org/>`_ as the documentation generator.

To build the docs, do::

    $ cd docs/
    $ make html

Please make changes to the documentation as required by the changes
you make.
