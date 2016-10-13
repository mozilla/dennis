import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    textclass = unicode
    from HTMLParser import HTMLParser, HTMLParseError  # noqa
    from itertools import izip_longest  # noqa

else:
    textclass = str
    from html.parser import HTMLParser  # noqa
    from itertools import zip_longest as izip_longest  # noqa
    try:
        from html.parser import HTMLParseError  # noqa
    except:
        # create a dummy class for Python 3.5+ where it's been removed
        # http://bugs.python.org/issue15114
        class HTMLParseError(Exception):
            pass
