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
