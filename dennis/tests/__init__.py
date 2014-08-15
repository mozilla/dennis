import contextlib
import shutil
import sys
import tempfile


def build_po_string(data):
    return (
        '#, fuzzy\n'
        'msgid ""\n'
        'msgstr ""\n'
        '"Project-Id-Version: foo\\n"\n'
        '"POT-Creation-Date: 2013-06-05 14:16-0700\\n"\n'
        '"PO-Revision-Date: 2010-04-26 18:00-0700\\n"\n'
        '"Last-Translator: Automatically generated\\n"\n'
        '"Language-Team: English\\n"\n'
        '"Language: \\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        '"X-Generator: Translate Toolkit 1.6.0\\n"\n\n'
        + data)


@contextlib.contextmanager
def tempdir():
    """Builds a tempdir and cleans up afterwards

    Usage::

        with tempdir() as dir_:
            # blah blah blah

    """
    dir_ = tempfile.mkdtemp()
    yield dir_
    shutil.rmtree(dir_)


@contextlib.contextmanager
def redirect(stdin=None, stdout=None, stderr=None):
    """Redirects stdin, stdout and stderr

    Usage::

        stdout = StringIO()
        stderr = StringIO()

        with redirect(stdout=stdout, stderr=stderr):
            print 'blah blah'


        # do soething with stdout.getvalue()

    """
    old_stdin = sys.stdin
    if stdin:
        sys.stdin = stdin
    old_stdout = sys.stdout
    if stdout:
        sys.stdout = stdout
    old_stderr = sys.stderr
    if stderr:
        sys.stderr = stderr

    yield

    sys.stdin = old_stdin
    sys.stdout = old_stdout
    sys.stderr = old_stderr
