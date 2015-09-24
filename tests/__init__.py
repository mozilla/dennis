POFILE_HEADER = """\
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: foo\\n"
"POT-Creation-Date: 2013-06-05 14:16-0700\\n"
"PO-Revision-Date: 2010-04-26 18:00-0700\\n"
"Last-Translator: Automatically generated\\n"
"Language-Team: English\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"X-Generator: Translate Toolkit 1.6.0\\n"
"""


def build_po_string(data):
    return POFILE_HEADER + '\n' + data
