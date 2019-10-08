import json
import pathlib
import shutil
import subprocess

import pytest

from manubot.util import shlex_join
from manubot.pandoc.util import (
    get_pandoc_version,
)


def test_cite_command_empty():
    process = subprocess.run(
        ['manubot', 'cite'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 2
    assert 'the following arguments are required: citekeys' in process.stderr


def test_cite_command_stdout():
    process = subprocess.run(
        ['manubot', 'cite', 'arxiv:1806.05726v1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(process.stderr)
    assert process.returncode == 0
    csl, = json.loads(process.stdout)
    assert csl['URL'] == 'https://arxiv.org/abs/1806.05726v1'


def test_cite_command_file(tmpdir):
    path = pathlib.Path(tmpdir) / 'csl-items.json'
    process = subprocess.run(
        ['manubot', 'cite', '--output', str(path), 'arxiv:1806.05726v1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(process.stderr.decode())
    assert process.returncode == 0
    with path.open() as read_file:
        csl, = json.load(read_file)
    assert csl['URL'] == 'https://arxiv.org/abs/1806.05726v1'


def cite_command_args():
    yield [], 'references-plain.txt'
    yield ['--format', 'plain'], 'references-plain.txt'
    yield ['--format', 'markdown'], 'references-markdown.md'
    yield ['--format', 'html'], 'references-html.html'
    if get_pandoc_version() == (2, 7, 3):
        xml = 'references-jats-2.7.3.xml'
    else:
        xml = 'references-jats.xml'
    yield ['--format', 'jats'], xml


def cite_command_rendered(filename: str):
    return (
        pathlib.Path(__file__).parent
        .joinpath('cite-command-rendered', filename)
        .read_text()
    )


@pytest.mark.parametrize(
    argnames=[
        'format_args',
        'expected_output'],
    argvalues=[
        (format_args, cite_command_rendered(filename)) 
        for format_args, filename in cite_command_args()],
    ids=[
        'no-args',
        '--format=plain',
        '--format=markdown',
        '--format=html',
        '--format=jats'])
@pytest.mark.skipif(
    not shutil.which('pandoc'),
    reason='pandoc installation not found on system'
)
@pytest.mark.skipif(
    not shutil.which('pandoc-citeproc'),
    reason='pandoc-citeproc installation not found on system'
)
def test_cite_command_render_stdout(format_args, expected_output):
    """
    Test the stdout output of `manubot cite --render` with various formats.
    The output is sensitive to the version of Pandoc used, so rather than fail when
    the system's pandoc is outdated, the test is skipped.
    """
    pandoc_version = get_pandoc_version()
    if pandoc_version < (2, 0):
        pytest.skip("Test requires pandoc >= 2.0 to support --lua-filter "
                    "and --csl=URL")
    for output in 'markdown', 'html', 'jats':
        if output in format_args and pandoc_version < (2, 5):
            pytest.skip(f"Test {output} output assumes pandoc >= 2.5")
    args = [
        'manubot', 'cite',
        '--render',
        '--csl', 'https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl',
        'arxiv:1806.05726v1', 'doi:10.7717/peerj.338', 'pmid:29618526',
    ] + format_args
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    print(shlex_join(process.args))
    print(process.stdout)
    print(process.stderr)
    assert process.stdout == expected_output


pandoc_version = get_pandoc_version() 

pytest.mark.skipif(pandoc_version < (2,0),
              reason="Test requires pandoc >= 2.0 to support --lua-filter and --csl=URL") 
class Test_cite_command_render_stdout():
    @classmethod
    def expected_output(cls, filename):
        return (
        pathlib.Path(__file__).parent
        .joinpath('cite-command-rendered', filename)
        .read_text()
    )
    
    @classmethod
    def _test_format_wtih_filename(self, format_args, filename):
        args = [
            'manubot', 'cite',
            '--render',
            '--csl', 'https://github.com/greenelab/manubot-rootstock/raw/e83e51dcd89256403bb787c3d9a46e4ee8d04a9e/build/assets/style.csl',
            'arxiv:1806.05726v1', 'doi:10.7717/peerj.338', 'pmid:29618526',
        ] + format_args
        process = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        print(shlex_join(process.args))
        print(process.stdout)
        print(process.stderr)
        assert process.stdout == self.expected_output(filename)
        
    def test_one(self):
        self._test_format_wtih_filename(['--format', 'plain'], 'references-plain.txt')
        
        
#    def test_jats(self):
#        if pandoc_version == (2, 7, 3):
#            filname = 'references-jats-2.7.3.xml'
#        else:
#            filname = 'references-jats.xml'
#        yield ['--format', 'jats'], xml


def teardown_module(module):
    """
    Avoid too many requests to NCBI E-Utils in the test_pubmed.py,
    which is executed following this module. E-Utility requests are
    capped at 3 per second, which is usually controled by _get_eutils_rate_limiter,
    but this does not seem to work across test modules.
    """
    import time
    time.sleep(1)
