import json
import logging
import pathlib
import shutil
import subprocess
import sys

# For manubot cite, infer --format from --output filename extensions
extension_to_format = {
    '.txt': 'plain',
    '.md': 'markdown',
    '.docx': 'docx',
    '.html': 'html',
    '.xml': 'jats',
}


def add_subparser_cite(subparsers):
    parser = subparsers.add_parser(
        name='cite',
        help='citation to CSL command line utility',
        description='Retrieve bibliographic metadata for one or more citation identifiers.',
    )
    parser.add_argument(
        '--render',
        action='store_true',
        help='Whether to render CSL Data into a formatted reference list using Pandoc. '
             'Pandoc version 2.0 or higher is required for complete support of available output formats.',
    )
    parser.add_argument(
        '--csl',
        default='https://github.com/greenelab/manubot-rootstock/raw/master/build/assets/style.csl',
        help="When --render, specify an XML CSL definition to style references (i.e. Pandoc's --csl option). "
             "Defaults to Manubot's style.",
    )
    parser.add_argument(
        '--format',
        choices=list(extension_to_format.values()),
        help="When --render, format to use for output file. "
             "If not specified, attempt to infer this from filename extension. "
             "Otherwise, default to plain.",
    )
    parser.add_argument(
        '--output',
        type=pathlib.Path,
        help='Specify a file to write output, otherwise default to stdout.',
    )
    parser.add_argument(
        '--allow-invalid-csl-data',
        dest='prune_csl',
        action='store_false',
        help='Allow CSL Items that do not conform to the JSON Schema. Skips CSL pruning.',
    )
    parser.add_argument(
        'citations',
        nargs='+',
        help='One or more (space separated) citations to produce CSL for.',
    )
    parser.set_defaults(function=cli_cite)
    return parser


def call_pandoc(metadata, path, format='plain'):
    """
    path is the path to write to.
    """
    info = _get_pandoc_info()
    _check_pandoc_version(info, metadata, format)
    metadata_block = '---\n{yaml}\n...\n'.format(
        yaml=json.dumps(metadata, ensure_ascii=False, indent=2)
    )
    args = [
        'pandoc',
        '--filter', 'pandoc-citeproc',
        '--output', str(path) if path else '-',
    ]
    if format == 'markdown':
        args.extend(['--to', 'markdown_strict'])
    elif format == 'jats':
        args.extend(['--to', 'jats', '--standalone'])
    elif format == 'docx':
        args.extend(['--to', 'docx'])
    elif format == 'html':
        args.extend(['--to', 'html'])
    elif format == 'plain':
        args.extend(['--to', 'plain'])
        if info['pandoc version'] >= (2,):
            # Do not use ALL_CAPS for bold & underscores for italics
            # https://github.com/jgm/pandoc/issues/4834#issuecomment-412972008
            filter_path = pathlib.Path(__file__).joinpath('..', 'plain-pandoc-filter.lua').resolve()
            assert filter_path.exists()
            args.extend(['--lua-filter', str(filter_path)])
    logging.info('call_pandoc subprocess args:\n' + ' '.join(args))
    process = subprocess.run(
        args=args,
        input=metadata_block.encode(),
        stdout=subprocess.PIPE if path else sys.stdout,
        stderr=sys.stderr,
    )
    process.check_returncode()


def cli_cite(args):
    """
    Main function for the manubot cite command-line interface.

    Does not allow user to directly specify Pandoc's --to argument, due to
    inconsistent citaiton rendering by output format. See
    https://github.com/jgm/pandoc/issues/4834
    """
    from manubot.cite.cite import (
        citation_to_citeproc,
        standardize_citation,
    )

    # generate CSL JSON data
    csl_list = list()
    for citation in args.citations:
        citation = standardize_citation(citation)
        csl_list.append(citation_to_citeproc(citation, prune=args.prune_csl))

    # output CSL JSON data, if --render is False
    if not args.render:
        write_file = args.output.open('w') if args.output else sys.stdout
        with write_file:
            json.dump(csl_list, write_file, ensure_ascii=False, indent=2)
            write_file.write('\n')
        return

    # use Pandoc to render citations
    if not args.format and args.output:
        vars(args)['format'] = extension_to_format.get(args.output.suffix)
    if not args.format:
        vars(args)['format'] = 'plain'
    pandoc_metadata = {
        'nocite': '@*',
        'csl': args.csl,
        'references': csl_list,
    }
    call_pandoc(
        metadata=pandoc_metadata,
        path=args.output,
        format=args.format,
    )


def _get_pandoc_info():
    """
    Return path and version information for the system's pandoc and
    pandoc-citeproc commands. If not available, exit program.
    """
    stats = dict()
    for command in 'pandoc', 'pandoc-citeproc':
        path = shutil.which(command)
        if not path:
            logging.critical(
                f'"{command}" not found on system. '
                f'Check that Pandoc is installed.'
            )
            raise SystemExit(1)
        version = subprocess.check_output(
            args=[command, '--version'],
            universal_newlines=True,
        )
        logging.debug(version)
        version, *discard = version.splitlines()
        discard, version = version.strip().split()
        version = tuple(map(int, version.split('.')))
        stats[f'{command} version'] = version
        stats[f'{command} path'] = path
    logging.info('\n'.join(f'{k}: {v}' for k, v in stats.items()))
    return stats


def _check_pandoc_version(info, metadata, format):
    """
    Given info from _get_pandoc_info, check that Pandoc's version is sufficient
    to perform the citation rendering command specified by metadata and format.
    Please add additional minimum version information to this function, as its
    discovered.
    """
    issues = list()
    if format == 'jats' and info['pandoc version'] < (2,):
        issues.append('--jats requires pandoc >= v2.0.')
    # --csl=URL did not work in https://travis-ci.org/greenelab/manubot/builds/417314743#L796, but exact version where this fails unknown
    # if metadata.get('csl', '').startswith('http') and pandoc_version < (2,):
    #     issues.append('--csl=URL requires pandoc >= v2.0.')
    issues = '\n'.join(issues)
    if issues:
        logging.critical(f'issues with pandoc version detected:\n{issues}')
