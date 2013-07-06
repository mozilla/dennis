from unittest import TestCase

from nose.tools import eq_

from dennis.tools import VariableTokenizer
from dennis.translator import (
    HTMLExtractorTransform, PirateTransform, Token, Translator)


class PirateTest(TestCase):
    vartok = VariableTokenizer(['python'])

    def test_basic(self):
        data = [
            (u'Hello',
             u'Hello ahoy\u2757'),

            (u'Hello %(username)s',
             u'Hello %(usarrname)s aye\u2757'),

            (u'Hello %s',
             u'Hello %s cap\'n\u2757'),

            (u'Hello {user}{name}',
             u'Hello {userr}{name} aye\u2757'),

            (u'Products and Services',
             u'Products and Services cap\'n\u2757'),

            (u'Get community support',
             u'Get community support cap\'n\u2757'),

            (u'Your input helps make Mozilla better',
             u'Your input helps make Mozilla better shiver me timbers\u2757'),

            (u'Super browsing',
             u'Super browsing arrRRr\u2757'),
        ]

        for text, expected in data:
            pt = PirateTransform()
            output = pt.transform(self.vartok, [Token(text)])
            output = u''.join([token.s for token in output])

            eq_(output, expected)


class HTMLExtractorTest(TestCase):
    vartok = VariableTokenizer(['python'])

    def test_basic(self):
        htmle = HTMLExtractorTransform()
        output = htmle.transform(self.vartok, [Token('')])
        eq_(output, [Token(u'', 'text', True)])

        output = htmle.transform(self.vartok, [Token('<b>hi</b>')])
        eq_(output,
            [
                Token(u'<b>', 'html', False),
                Token(u'hi', 'text', True),
                Token(u'</b>', 'html', False),
            ]
        )

    def test_alt_title(self):
        htmle = HTMLExtractorTransform()
        output = htmle.transform(self.vartok, [
                Token('<img alt="foo">')])
        eq_(output,
            [
                Token(u'<img alt="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )

        output = htmle.transform(self.vartok, [
                Token('<img title="foo">')])
        eq_(output,
            [
                Token(u'<img title="', 'html', False),
                Token(u'foo', 'text', True),
                Token(u'">', 'html', False),
            ]
        )


class TranslatorTest(TestCase):
    def test_pirate_translate(self):
        trans = Translator(['python'], ['pirate'])
        eq_(trans.translate_string(u'hello'),
            u'hello ahoy\u2757')

        # Note, this doesn't work right because it's not accounting
        # for html. But it's correct for this test.
        eq_(trans.translate_string(u'<b>hello</b>'),
            u'<b>hello</b> prepare to be boarded\u2757')

    def test_html_pirate_translate(self):
        trans = Translator(['python'], ['html', 'pirate'])
        eq_(trans.translate_string(u'<b>hello</b>'),
            u'<b>hello ahoy\u2757</b>')
