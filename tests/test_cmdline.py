from click.testing import CliRunner
import pytest

from dennis.cmdline import cli


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

    # FIXME: test --varformat

    # FIXME: test --pipeline


class TestLint:
    def test_help(self, runner):
        result = runner.invoke(cli, ('lint', '--help'))
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]

    # FIXME: test --varformat on .po file

    # FIXME: test --rules on .po file

    # FIXME: test --reporter

    # FIXME: test --errorsonly
