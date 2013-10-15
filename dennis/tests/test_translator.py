from unittest import TestCase

from nose.tools import eq_

from dennis.tools import VariableTokenizer
from dennis.translator import (
    AngleQuoteTransform,
    DubstepTransform,
    EmptyTransform,
    HTMLExtractorTransform,
    HahaTransform,
    PirateTransform,
    RedactedTransform,
    ShoutyTransform,
    Token,
    Translator,
    XXXTransform
)


class TransformTestCase(TestCase):
    vartok = VariableTokenizer(['python'])


class EmptyTransformTest(TransformTestCase):
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

            eq_(output, expected)


class HahaTransformTest(TransformTestCase):
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

            eq_(output, expected)


class PirateTransformTest(TransformTestCase):
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

            eq_(output, expected)


class DubstepTransformTest(TransformTestCase):
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

            eq_(output, expected)


class HTMLExtractorTest(TestCase):
    vartok = VariableTokenizer(['python'])

    def test_basic(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [Token('')])
        eq_(output, [Token(u'', 'text', True)])

        output = trans.transform(self.vartok, [Token('<b>hi</b>')])
        eq_(output,
            [
                Token(u'<b>', 'html', False),
                Token(u'hi', 'text', True),
                Token(u'</b>', 'html', False),
            ]
        )

    def test_alt_title(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [
                Token('<img alt="foo">')])
        eq_(output,
            [
                Token(u'<img alt="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )

        output = trans.transform(self.vartok, [
                Token('<img title="foo">')])
        eq_(output,
            [
                Token(u'<img title="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )


class XXXTransformTest(TransformTestCase):
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

            eq_(output, expected)


class AngleQuoteTransformTest(TransformTestCase):
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

            eq_(output, expected)


class ShoutyTransformTest(TransformTestCase):
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

            eq_(output, expected)


class RedactedTransformTest(TransformTestCase):
    def test_basic(self):
        data = [
            (u'Hello', u'Xxxxx'),
            (u'OMG!', u'XXX!'),
        ]

        for text, expected in data:
            trans = RedactedTransform()
            output = trans.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            eq_(output, expected)


class TranslatorTest(TestCase):
    def test_pirate_translate(self):
        trans = Translator(['python'], ['pirate'])
        eq_(trans.translate_string(u'hello'),
            u'\'ello ahoy\u2757')

        # Note, this doesn't work right because it's not accounting
        # for html. But it's correct for this test.
        eq_(trans.translate_string(u'<b>hello</b>'),
            u'<b>\'ello</b> prepare to be boarded\u2757')

    def test_html_pirate_translate(self):
        trans = Translator(['python'], ['html', 'pirate'])
        eq_(trans.translate_string(u'<b>hello</b>'),
            u'<b>\'ello ahoy\u2757</b>')

    def test_shouty_html_pirate_translate(self):
        trans = Translator(['python'], ['shouty', 'html', 'pirate'])
        eq_(trans.translate_string(u'<b>hello.</b>\n'),
            u'<b>HELLO aye\u2757.</b>\n')
