from click.testing import CliRunner
import pytest

from dennis.cmdline import cli
from tests import build_po_string


@pytest.fixture
def runner():
    """Creates a CliRunner"""
    return CliRunner()


def build_key_val(text):
    pairs = {}
    for line in text.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            pairs[key.strip()] = val.strip()
    return pairs


class TestStatus:
    def test_help(self, runner):
        result = runner.invoke(cli, ('status', '--help'))
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]

    def test_status_untranslated(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo bar baz"\n'
            'msgstr ""\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)

        result = runner.invoke(cli, ('status', str(fn)))
        assert result.exit_code == 0

        # FIXME: This would be a lot easier if the status was
        # structured and parseable.
        pairs = build_key_val(result.output)
        assert pairs['Total strings'] == '1'
        assert pairs['Total translateable words'] == '3'
        assert pairs['Percentage'] == '0%'

    def test_status_translated(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo bar baz"\n'
            'msgstr "Feh"\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)

        result = runner.invoke(cli, ('status', str(fn)))
        assert result.exit_code == 0

        # FIXME: This would be a lot easier if the status was
        # structured and parseable.
        pairs = build_key_val(result.output)
        assert pairs['Total strings'] == '1'
        assert pairs['Total translateable words'] == '3'
        assert pairs['Percentage'] == '100% COMPLETE!'

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

    def test_no_paths(self, runner):
        result = runner.invoke(cli, ('translate', '-p', 'shouty'))
        assert result.exit_code == 2
        last_line = result.output.splitlines()[-1]
        assert last_line == 'Error: nothing to work on. Use --help for help.'

    def test_pipe(self, runner):
        result = runner.invoke(cli, ('translate', '-p', 'shouty', '-'), input='foo bar')
        assert result.exit_code == 0
        assert result.output == 'FOO BAR\n'

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


class TestLint:
    def test_help(self, runner):
        result = runner.invoke(cli, ('lint', '--help'))
        assert result.exit_code == 0
        assert 'Usage' in result.output.splitlines()[0]

    def test_basic_linting(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo bar baz"\n'
            'msgstr "Foo"\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)

        result = runner.invoke(cli, ('lint', str(fn)))
        assert result.exit_code == 0
        output_lines = result.output.splitlines()
        assert len(output_lines) == 1
        assert output_lines[0].startswith('dennis version')

    def test_linting_fail(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo %(foo)s bar baz"\n'
            'msgstr "Foo %(bar)s"\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)

        result = runner.invoke(cli, ('lint', str(fn)))
        assert result.exit_code == 1
        output_lines = result.output.splitlines()
        assert len(output_lines) == 16
        assert 'E201: invalid variables: %(bar)s' in result.output

    def test_no_files_to_work_on(self, runner):
        result = runner.invoke(cli, ('lint', 'foo'))
        assert result.exit_code == 2
        assert 'nothing to work on.' in result.output

    def test_nonexistent_file(self, runner, tmpdir):
        fn = tmpdir.join('missingfile.po')
        result = runner.invoke(cli, ('lint', str(fn)))
        assert result.exit_code == 2
        last_line = result.output.splitlines()[-1]
        assert last_line == 'Error: file "%s" does not exist.' % str(fn)

    def test_quiet(self, runner, tmpdir):
        po_file = build_po_string(
            '#: foo/foo.py:5\n'
            'msgid "Foo bar baz"\n'
            'msgstr "Foo"\n')
        fn = tmpdir.join('messages.po')
        fn.write(po_file)

        result = runner.invoke(cli, ('lint', '--quiet', str(fn)))
        assert result.exit_code == 0
        assert result.output == ''

    # FIXME: test --varformat on .po file

    # FIXME: test --rules on .po file

    # FIXME: test --reporter

    # FIXME: test --errorsonly
