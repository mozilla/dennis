from click.testing import CliRunner
import pytest

from dennis.cmdline import cli
from tests import build_po_string


@pytest.fixture
def runner():
    """Creates a CliRunner"""
    return CliRunner()


class TestStatus:
    def test_help(self, runner):
        result = runner.invoke(cli, ('status', '--help'))
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]

    # FIXME: test status on .po file

    # FIXME: test --showuntranslated on .po file

    # FIXME: test --showfuzzy on .po file


class TestTranslate:
    def test_help(self, runner):
        result = runner.invoke(cli, ('translate', '--help'))
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]

    def test_strings(self, runner):
        result = runner.invoke(cli, ('translate', '-p', 'shouty', '-s', 'ou812'))
        assert result.exit_code == 0
        assert 'OU812' in result.output

    def test_pipeline(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo bar baz"\n'
            'msgstr ""\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)
        # Verify the last line is untranslated
        assert po_file.endswith('msgstr ""\n')

        result = runner.invoke(cli, ('translate', '-p', 'shouty', str(fn)))
        assert result.exit_code == 0
        last_line = fn.read().splitlines()[-1]
        # Verify the last line is now translated
        assert last_line == 'msgstr "FOO BAR BAZ"'

    def test_bad_pipeline(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo bar baz"\n'
            'msgstr ""\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)

        result = runner.invoke(cli, ('translate', '-p', 'triangle', str(fn)))
        assert result.exit_code == 2
        last_line = result.output.splitlines()[-1]
        assert last_line == 'Error: pipeline "triangle" is not valid'

    def test_nonexistent_file(self, runner, tmpdir):
        fn = tmpdir.join('missingfile.po')
        result = runner.invoke(cli, ('translate', '-p', 'shouty', str(fn)))
        assert result.exit_code == 2
        last_line = result.output.splitlines()[-1]
        assert last_line == 'Error: file %s does not exist.' % str(fn)

    # FIXME: test --varformat


class TestLint:
    def test_help(self, runner):
        result = runner.invoke(cli, ('lint', '--help'))
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]

    # FIXME: test --varformat on .po file

    # FIXME: test --rules on .po file

    # FIXME: test --reporter

    # FIXME: test --errorsonly
