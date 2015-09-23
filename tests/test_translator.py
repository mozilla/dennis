from dennis.tools import VariableTokenizer
from dennis.translator import (
    AngleQuoteTransform,
    DubstepTransform,
    EmptyTransform,
    HTMLExtractorTransform,
    HahaTransform,
    PirateTransform,
    RedactedTransform,
    ReverseTransform,
    ShoutyTransform,
    Token,
    Translator,
    DoubleTransform,
    XXXTransform,
    ZombieTransform
)


class TransformTestCase:
    vartok = VariableTokenizer(['python-format', 'python-brace-format'])


class TestEmptyTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u''),
            (u'OMG!', u''),
            (u'', u'')
        ]

        for text, expected in data:
            trans = EmptyTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestHahaTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'Haha\u2757 Hello'),
            (u'OMG! Hello!', u'Haha\u2757 OMG! Haha\u2757 Hello!'),
            (u'', u'Haha\u2757 '),
            (u'Hi!\nHello!', u'Haha\u2757 Hi!\nHaha\u2757 Hello!'),
        ]

        for text, expected in data:
            trans = HahaTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestPirateTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello',
             u'\'ello ahoy\u2757'),

            (u'Hello %(username)s',
             u'\'ello %(username)s ahoy\u2757'),

            (u'Hello %s',
             u'\'ello %s cap\'n\u2757'),

            (u'Hello {user}{name}',
             u'\'ello {user}{name} ahoy\u2757'),

            (u'Products and Services',
             u'Products and Sarrvices yo-ho-ho\u2757'),

            (u'Get community support',
             u'Get community supparrt yo-ho-ho\u2757'),

            (u'Your input helps make Mozilla better',
             u'Yerr input \'elps make Mozillar betterr prepare to '
             u'be boarded\u2757'),

            (u'Super browsing',
             u'Superr browsin\' arrRRRrrr\u2757'),
        ]

        for text, expected in data:
            trans = PirateTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestDubstepTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello',
             u'Hello t-t-t-t\u2757'),

            (u'Hello %(username)s',
             u'Hello t-t-t-t %(username)s BWWWWWWAAAAAAAAaaaaaa\u2757'),

            (u'Hello %s',
             u'Hello t-t-t-t %s BWWWWAAAAAaaaa\u2757'),

            (u'Hello {user}{name}',
             u'Hello t-t-t-t {user}{name} BWWWWWWAAAAAAAAaaaaaa\u2757'),

            (u'Products and Services',
             u'Products and Services BWWWWWAAAAAAAaaaaa\u2757'),

            (u'Get community support',
             (u'Get t-t-t-t community BWWWWWAAAAAAAaaaaa support '
              u'V\u221eP V\u221eP\u2757')),

            (u'Your input helps make Mozilla better',
             (u'Your input helps make BWWWWWAAAAAAAaaaaa Mozilla '
              u'....vvvVV better BWWWWWWAAAAAAAAaaaaaa\u2757')),

            (u'Super browsing',
             u'Super t-t-t-t browsing BWWWWWAAAAAAAaaaaa\u2757'),
        ]

        for text, expected in data:
            trans = DubstepTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestZombieTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'', u''),
            (u'Hello', u'HHAMNMNHR RARRR!!!'),
            (u'Hi\nHello', u'HAR\nHHAMNMNHR BR-R-R-RAINS!'),
            (u'Hi   \nHello!\nmultiline',
             u'HAR   \nHHAMNMNHR\u2757\nmNMMNHGARMNARnHA'),
            (u'Hello %(username)s', u'HHAMNMNHR %(username)s'),
            (u'Hello %s', u'HHAMNMNHR %s GRRRRRrrRR!!'),
            (u'Hello {user}{name}', u'HHAMNMNHR {user}{name}'),
            (u'Products and Services',
             u'PMZHRGBNMZZHGRZ anGB SHAMZBBARZZHARZ'),
            (u'Get community support',
             u'GHAHG ZZHRmmNMnARHGRA RZNMBZBZHRMZHG'),
            (u'Your input helps make Mozilla better',
             (u'YHRNMMZ ARnBZNMHG hHAMNBZRZ maBGHA MHRzARMNMNa bHAHGHGHAMZ '
              'BR-R-R-RAINS!')),
            (u'Super browsing', u'SNMBZHAMZ bMZHRZMRZARng'),
        ]

        for text, expected in data:
            trans = ZombieTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestHTMLExtractor:
    vartok = VariableTokenizer(['python-format', 'python-brace-format'])

    def test_basic(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [Token('')])
        assert output == [Token(u'', 'text', True)]

        output = trans.transform(self.vartok, [Token('<b>hi</b>')])
        assert (
            output ==
            [
                Token(u'<b>', 'html', False),
                Token(u'hi', 'text', True),
                Token(u'</b>', 'html', False),
            ]
        )

    def test_alt_title_placeholder(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [
            Token('<img alt="foo">')])
        assert (
            output ==
            [
                Token(u'<img alt="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )

        output = trans.transform(self.vartok, [
            Token('<img title="foo">')])
        assert (
            output ==
            [
                Token(u'<img title="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )

        output = trans.transform(self.vartok, [
            Token('<input placeholder="foo">')])
        assert (
            output ==
            [
                Token(u'<input placeholder="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )

    def test_script_style(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [
            Token('<style>TR {white-space: nowrap;}</style>')
        ])
        assert (
            output ==
            [
                Token(u'<style>', 'html', False),
                Token(u'TR {white-space: nowrap;}', 'style', False),
                Token(u'</style>', 'html', False)
            ]
        )

        output = trans.transform(self.vartok, [
            Token('<script>console.log("foo");</script>')
        ])
        assert (
            output ==
            [
                Token(u'<script>', 'html', False),
                Token(u'console.log("foo");', 'script', False),
                Token(u'</script>', 'html', False)
            ]
        )


class TestXXXTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'xxxHelloxxx'),
            (u'OMG!', u'xxxOMG!xxx'),
            (u'Line\nWith\nCRs', u'xxxLinexxx\nxxxWithxxx\nxxxCRsxxx'),
            (u'Line.  \nWith!\nCRs', u'xxxLine.xxx  \nxxxWith!xxx\nxxxCRsxxx')
        ]

        for text, expected in data:
            trans = XXXTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestDoubleTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'Heelloo'),
            (u'OMG!', u'OOMG!'),
            (u'Line\nWith\nCRs', u'Liinee\nWiith\nCRs'),
        ]

        for text, expected in data:
            trans = DoubleTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestAngleQuoteTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'\xabHello\xbb'),
            (u'OMG!', u'\xabOMG!\xbb'),
            (u'Line\nWith\nCRs', u'\xabLine\nWith\nCRs\xbb'),
            (u'Line.  \nWith!\nCRs', u'\xabLine.  \nWith!\nCRs\xbb'),
        ]

        for text, expected in data:
            trans = AngleQuoteTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestShoutyTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'HELLO'),
            (u'OMG!', u'OMG!'),
            (u'<b>Hello.</b>', u'<B>HELLO.</B>'),
        ]

        for text, expected in data:
            trans = ShoutyTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestReverseTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'olleH'),
            (u'OMG!', u'!GMO'),
            (u'Hello. This is a test.', u'.tset a si sihT .olleH'),
        ]

        for text, expected in data:
            trans = ReverseTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestRedactedTransform(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'Xxxxx'),
            (u'OMG!', u'XXX!'),
        ]

        for text, expected in data:
            trans = RedactedTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            assert output == expected


class TestTranslator:
    def test_pirate_translate(self):
        trans = Translator(
            ['python-format', 'python-brace-format'],
            ['pirate']
        )
        assert (
            trans.translate_string(u'hello') ==
            u'\'ello ahoy\u2757'
        )

        # Note, this doesn't work right because it's not accounting
        # for html. But it's correct for this test.
        assert (
            trans.translate_string(u'<b>hello</b>') ==
            u'<b>\'ello</b> prepare to be boarded\u2757'
        )

    def test_html_pirate_translate(self):
        trans = Translator(
            ['python-format', 'python-brace-format'],
            ['html', 'pirate']
        )
        assert (
            trans.translate_string(u'<b>hello</b>') ==
            u'<b>\'ello ahoy\u2757</b>'
        )

    def test_shouty_html_pirate_translate(self):
        trans = Translator(
            ['python-format', 'python-brace-format'],
            ['shouty', 'html', 'pirate']
        )
        assert (
            trans.translate_string(u'<b>hello.</b>\n') ==
            u'<b>HELLO aye\u2757.</b>\n'
        )
