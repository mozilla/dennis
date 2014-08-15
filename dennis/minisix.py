import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    textclass = unicode
    from HTMLParser import HTMLParser
    from itertools import izip_longest
    from StringIO import StringIO

else:
    textclass = str
    from html.parser import HTMLParser
    from io import StringIO
    from itertools import zip_longest as izip_longest
