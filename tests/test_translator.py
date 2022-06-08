import pytest

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
    ZombieTransform,
)


class TransformTestCase:
    vartok = VariableTokenizer(["python-format", "python-brace-format"])


class TestEmptyTransform(TransformTestCase):
    @pytest.mark.parametrize("text,expected", [("Hello", ""), ("OMG!", ""), ("", "")])
    def test_basic(self, text, expected):
        trans = EmptyTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestHahaTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "Haha\u2757 Hello"),
            ("OMG! Hello!", "Haha\u2757 OMG! Haha\u2757 Hello!"),
            ("", "Haha\u2757 "),
            ("Hi!\nHello!", "Haha\u2757 Hi!\nHaha\u2757 Hello!"),
        ],
    )
    def test_basic(self, text, expected):
        trans = HahaTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestPirateTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "'ello ahoy\u2757"),
            ("Hello %(username)s", "'ello %(username)s ahoy\u2757"),
            ("Hello %s", "'ello %s cap'n\u2757"),
            ("Hello {user}{name}", "'ello {user}{name} ahoy\u2757"),
            ("Products and Services", "Products and Sarrvices yo-ho-ho\u2757"),
            ("Get community support", "Get community supparrt yo-ho-ho\u2757"),
            (
                "Your input helps make Mozilla better",
                "Yerr input 'elps make Mozillar betterr prepare to be boarded\u2757",
            ),
            ("Super browsing", "Superr browsin' arrRRRrrr\u2757"),
        ],
    )
    def test_basic(self, text, expected):
        trans = PirateTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestDubstepTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "Hello t-t-t-t\u2757"),
            (
                "Hello %(username)s",
                "Hello t-t-t-t %(username)s BWWWWWWAAAAAAAAaaaaaa\u2757",
            ),
            ("Hello %s", "Hello t-t-t-t %s BWWWWAAAAAaaaa\u2757"),
            (
                "Hello {user}{name}",
                "Hello t-t-t-t {user}{name} BWWWWWWAAAAAAAAaaaaaa\u2757",
            ),
            ("Products and Services", "Products and Services BWWWWWAAAAAAAaaaaa\u2757"),
            (
                "Get community support",
                (
                    "Get t-t-t-t community BWWWWWAAAAAAAaaaaa support V\u221eP V\u221eP\u2757"
                ),
            ),
            (
                "Your input helps make Mozilla better",
                (
                    "Your input helps make BWWWWWAAAAAAAaaaaa Mozilla "
                    "....vvvVV better BWWWWWWAAAAAAAAaaaaaa\u2757"
                ),
            ),
            ("Super browsing", "Super t-t-t-t browsing BWWWWWAAAAAAAaaaaa\u2757"),
            (
                "Sentence 1. Sentence 2!",
                "Sentence 1 . t-t-t-t Sentence 2! BWWWWWWWWAAAAAAAAAAaaaaaaaa\u2757",
            ),
        ],
    )
    def test_basic(self, text, expected):
        trans = DubstepTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestZombieTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("", ""),
            ("Hello", "HHAMNMNHR RARRR!!!"),
            ("Hi\nHello", "HAR\nHHAMNMNHR BR-R-R-RAINS!"),
            ("Hi   \nHello!\nmultiline", "HAR   \nHHAMNMNHR\u2757\nmNMMNHGARMNARnHA"),
            ("Hello %(username)s", "HHAMNMNHR %(username)s"),
            ("Hello %s", "HHAMNMNHR %s GRRRRRrrRR!!"),
            # FIXME: This is a problem where variables from the variable tokenizer should
            # be treated as immutable tokens and right now they aren't. Issue #67.
            ("Hello {user}{name}", "HHAMNMNHR {user}{namHA}"),
            ("Products and Services", "PMZHRGBNMZZHGRZ anGB SHAMZBBARZZHARZ"),
            ("Get community support", "GHAHG ZZHRmmNMnARHGRA RZNMBZBZHRMZHG"),
            (
                "Your input helps make Mozilla better",
                (
                    "YHRNMMZ ARnBZNMHG hHAMNBZRZ maBGHA MHRzARMNMNa bHAHGHGHAMZ "
                    "BR-R-R-RAINS!"
                ),
            ),
            ("Super browsing", "SNMBZHAMZ bMZHRZMRZARng"),
        ],
    )
    def test_basic(self, text, expected):
        trans = ZombieTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestHTMLExtractor:
    vartok = VariableTokenizer(["python-format", "python-brace-format"])

    def test_basic(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [Token("")])
        assert output == [Token("", "text", True)]

        output = trans.transform(self.vartok, [Token("<b>hi</b>")])
        assert output == [
            Token("<b>", "html", False),
            Token("hi", "text", True),
            Token("</b>", "html", False),
        ]

    def test_alt_title_placeholder(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(self.vartok, [Token('<img alt="foo">')])
        assert output == [
            Token('<img alt="', "html", False),
            Token("foo", "text", True),
            Token('">', "html", False),
        ]

        output = trans.transform(self.vartok, [Token('<img title="foo">')])
        assert output == [
            Token('<img title="', "html", False),
            Token("foo", "text", True),
            Token('">', "html", False),
        ]

        output = trans.transform(self.vartok, [Token('<input placeholder="foo">')])
        assert output == [
            Token('<input placeholder="', "html", False),
            Token("foo", "text", True),
            Token('">', "html", False),
        ]

    def test_script_style(self):
        trans = HTMLExtractorTransform()
        output = trans.transform(
            self.vartok, [Token("<style>TR {white-space: nowrap;}</style>")]
        )
        assert output == [
            Token("<style>", "html", False),
            Token("TR {white-space: nowrap;}", "style", False),
            Token("</style>", "html", False),
        ]

        output = trans.transform(
            self.vartok, [Token('<script>console.log("foo");</script>')]
        )
        assert output == [
            Token("<script>", "html", False),
            Token('console.log("foo");', "script", False),
            Token("</script>", "html", False),
        ]

    def test_whitespace_collapse(self):
        def _trans(text):
            return HTMLExtractorTransform().transform(self.vartok, [Token(text)])

        assert _trans("<html><body>hello!</body></html>") == _trans(
            "<html><body>    hello!    </body></html>"
        )


class TestXXXTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "xxxHelloxxx"),
            ("OMG!", "xxxOMG!xxx"),
            ("Line\nWith\nCRs", "xxxLinexxx\nxxxWithxxx\nxxxCRsxxx"),
            ("Line.  \nWith!\nCRs", "xxxLine.xxx  \nxxxWith!xxx\nxxxCRsxxx"),
        ],
    )
    def test_basic(self, text, expected):
        trans = XXXTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestDoubleTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "Heelloo"),
            ("OMG!", "OOMG!"),
            ("Line\nWith\nCRs", "Liinee\nWiith\nCRs"),
        ],
    )
    def test_basic(self, text, expected):
        trans = DoubleTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestAngleQuoteTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "\xabHello\xbb"),
            ("OMG!", "\xabOMG!\xbb"),
            ("Line\nWith\nCRs", "\xabLine\nWith\nCRs\xbb"),
            ("Line.  \nWith!\nCRs", "\xabLine.  \nWith!\nCRs\xbb"),
        ],
    )
    def test_basic(self, text, expected):
        trans = AngleQuoteTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestShoutyTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [("Hello", "HELLO"), ("OMG!", "OMG!"), ("<b>Hello.</b>", "<B>HELLO.</B>")],
    )
    def test_basic(self, text, expected):
        trans = ShoutyTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestReverseTransform(TransformTestCase):
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello", "olleH"),
            ("OMG!", "!GMO"),
            ("Hello. This is a test.", ".tset a si sihT .olleH"),
        ],
    )
    def test_basic(self, text, expected):
        trans = ReverseTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestRedactedTransform(TransformTestCase):
    @pytest.mark.parametrize("text,expected", [("Hello", "Xxxxx"), ("OMG!", "XXX!")])
    def test_basic(self, text, expected):
        trans = RedactedTransform()
        output = trans.transform(self.vartok, [Token(text)])
        output = "".join([token.s for token in output])

        assert output == expected


class TestTranslator:
    def test_pirate_translate(self):
        trans = Translator(["python-format", "python-brace-format"], ["pirate"])
        assert trans.translate_string("hello") == "'ello ahoy\u2757"

        # Note, this doesn't work right because it's not accounting
        # for html. But it's correct for this test.
        assert (
            trans.translate_string("<b>hello</b>")
            == "<b>'ello</b> prepare to be boarded\u2757"
        )

    def test_html_pirate_translate(self):
        trans = Translator(["python-format", "python-brace-format"], ["html", "pirate"])
        assert trans.translate_string("<b>hello</b>") == "<b>'ello ahoy\u2757</b>"

    def test_shouty_html_pirate_translate(self):
        trans = Translator(
            ["python-format", "python-brace-format"], ["shouty", "html", "pirate"]
        )
        assert trans.translate_string("<b>hello.</b>\n") == "<b>HELLO aye\u2757.</b>"
