# Python utilities for Manubot: Manuscripts, open and automated

[![Travis Linux Build Status](https://travis-ci.com/manubot/manubot.svg?branch=master)](https://travis-ci.com/manubot/manubot)
[![AppVeyor Windows Build Status](https://ci.appveyor.com/api/projects/status/f20hvc6si5uiqd7e/branch/master?svg=true)](https://ci.appveyor.com/project/manubot/manubot/branch/master)

[Manubot](https://manubot.org/ "Manubot homepage") is a workflow and set of tools for the next generation of scholarly publishing.
This repository contains a Python package with several Manubot-related utilities, as described in the [usage section](#usage) below.

The `manubot cite` command-line interface retrieves and formats bibliographic metadata for user-supplied persistent identifiers like DOIs or PubMed IDs.
The `manubot process` command-line interface prepares scholarly manuscripts for Pandoc consumption.
The `manubot process` command is used by Manubot manuscripts, which are based off the [Rootstock template](https://github.com/manubot/rootstock), to automate several aspects of manuscript generation.
See Rootstock's [manuscript usage guide](https://github.com/manubot/rootstock/blob/master/USAGE.md) for more information.

**Note:**
If you want to experience Manubot by editing an existing manuscript, see <https://github.com/manubot/try-manubot>.
If you want to create a new manuscript, see <https://github.com/manubot/rootstock>.

To cite the Manubot project or for more information on its design and history, see:

> **Open collaborative writing with Manubot**<br>
Daniel S. Himmelstein, Vincent Rubinetti, David R. Slochower, Dongbo Hu, Venkat S. Malladi, Casey S. Greene, Anthony Gitter<br>
*PLOS Computational Biology* (2019-06-24) <https://doi.org/c7np><br>
DOI: [10.1371/journal.pcbi.1007128](https://doi.org/10.1371/journal.pcbi.1007128) · PMID: [31233491](https://www.ncbi.nlm.nih.gov/pubmed/31233491) · PMCID: [PMC6611653](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6611653)

The Manubot version of this manuscript is available at <https://greenelab.github.io/meta-review/>.

## Installation

If you are using the `manubot` Python package as part of a manuscript repository, installation of this package is handled though the Rootstock's [environment specification](https://github.com/manubot/rootstock/blob/master/build/environment.yml).
For other use cases, this package can be installed via `pip`.

Install the latest release version [from PyPI](https://pypi.org/project/manubot/):

```sh
pip install --upgrade manubot
```

Or install from the source code on [GitHub](https://github.com/manubot/manubot), using the version specified by a commit hash:

```sh
COMMIT=d2160151e52750895571079a6e257beb6e0b1278
pip install --upgrade git+https://github.com/manubot/manubot@$COMMIT
```

The `--upgrade` argument ensures `pip` updates an existing `manubot` installation if present.

## Usage

Installing the python package creates the `manubot` command line program.
Here is the usage information as per `manubot --help`:

<!-- test codeblock contains output of `manubot --help` -->
```
usage: manubot [-h] [--version] {process,cite} ...

Manubot: the manuscript bot for scholarly writing

optional arguments:
  -h, --help      show this help message and exit
  --version       show program's version number and exit

subcommands:
  All operations are done through subcommands:

  {process,cite}
    process       process manuscript content
    cite          citation to CSL command line utility
```

Note that all operations are done through the following sub-commands.

### Process

The `manubot process` program is the primary interface to using Manubot.
There are two required arguments: `--content-directory` and `--output-directory`, which specify the respective paths to the content and output directories.
The content directory stores the manuscript source files.
Files generated by Manubot are saved to the output directory.

One common setup is to create a directory for a manuscript that contains both the `content` and `output` directory.
Under this setup, you can run the Manubot using:

```sh
manubot process \
  --content-directory=content \
  --output-directory=output
```

See `manubot process --help` for documentation of all command line arguments:

<!-- test codeblock contains output of `manubot process --help` -->
```
usage: manubot process [-h] --content-directory CONTENT_DIRECTORY
                       --output-directory OUTPUT_DIRECTORY
                       [--template-variables-path TEMPLATE_VARIABLES_PATH]
                       [--cache-directory CACHE_DIRECTORY]
                       [--clear-requests-cache]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

Process manuscript content to create outputs for Pandoc consumption. Performs
bibliographic processing and templating.

optional arguments:
  -h, --help            show this help message and exit
  --content-directory CONTENT_DIRECTORY
                        Directory where manuscript content files are located.
  --output-directory OUTPUT_DIRECTORY
                        Directory to output files generated by this script.
  --template-variables-path TEMPLATE_VARIABLES_PATH
                        Path or URL of a JSON file containing template
                        variables for jinja2. Specify this argument multiple
                        times to read multiple files. Variables can be applied
                        to a namespace (i.e. stored under a dictionary key)
                        like `--template-variables-
                        path=namespace=path_or_url`. Namespaces must match the
                        regex `[a-zA-Z_][a-zA-Z0-9_]*`.
  --cache-directory CACHE_DIRECTORY
                        Custom cache directory. If not specified, caches to
                        output-directory.
  --clear-requests-cache
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level for stderr logging
```

#### Manual references

Manubot has the ability to rely on user-provided reference metadata rather than generating it.
`manubot process` searches the content directory for files containing manually-provided reference metadata that match the glob `manual-references*.*`.
If a manual reference filename ends with `.json` or `.yaml`, it's assumed to contain CSL Data (i.e. Citation Style Language JSON).
Otherwise, the format is inferred from the extension and converted to CSL JSON using the `pandoc-citeproc --bib2json` [utility](https://github.com/jgm/pandoc-citeproc/blob/master/man/pandoc-citeproc.1.md#convert-mode).
The standard citation for manual references is inferred from the CSL JSON `id` or `note` field.
When no prefix is provided, such as `doi:`, `url:`, or `raw:`, a `raw:` prefix is automatically added.
If multiple manual reference files load metadata for the same standard citation `id`, precedence is assigned according to descending filename order.

### Cite

`manubot cite` is a command line utility to create [CSL JSON items](http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html#items) for one or more citations.
Citations should be in the format `source:identifier`.
For example, the following example generates CSL JSON for four references:

```sh
manubot cite doi:10.1098/rsif.2017.0387 pmid:29424689 pmcid:PMC5640425 arxiv:1806.05726
```

The following [terminal recording](https://asciinema.org/a/205085?speed=2) demonstrates the main features of `manubot cite`:

![manubot cite demonstration](media/terminal-recordings/manubot-cite-cast.gif)

Additional usage information is available from `manubot cite --help`:

<!-- test codeblock contains output of `manubot cite --help` -->
```
usage: manubot cite [-h] [--render] [--csl CSL]
                    [--format {plain,markdown,docx,html,jats}]
                    [--output OUTPUT] [--allow-invalid-csl-data]
                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                    citekeys [citekeys ...]

Retrieve bibliographic metadata for one or more citation identifiers.

positional arguments:
  citekeys              One or more (space separated) citation keys to produce
                        CSL for.

optional arguments:
  -h, --help            show this help message and exit
  --render              Whether to render CSL Data into a formatted reference
                        list using Pandoc. Pandoc version 2.0 or higher is
                        required for complete support of available output
                        formats.
  --csl CSL             When --render, specify an XML CSL definition to style
                        references (i.e. Pandoc's --csl option). Defaults to
                        Manubot's style.
  --format {plain,markdown,docx,html,jats}
                        When --render, format to use for output file. If not
                        specified, attempt to infer this from filename
                        extension. Otherwise, default to plain.
  --output OUTPUT       Specify a file to write output, otherwise default to
                        stdout.
  --allow-invalid-csl-data
                        Allow CSL Items that do not conform to the JSON
                        Schema. Skips CSL pruning.
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level for stderr logging
```

## Development

Create a development environment using:

```sh
conda create --name manubot-dev --channel conda-forge \
  python=3.6 jinja2 pandas pytest pandoc
conda activate manubot-dev  # assumes conda >= 4.4
pip install --editable .
```

Inside this environment, use `pytest` to run the test suite.
You can also use the `manubot` CLI to build manuscripts.
For example:

```sh
manubot process \
  --content-directory=tests/manuscripts/example/content \
  --output-directory=tests/manuscripts/example/output \
  --log-level=DEBUG
```

## Release instructions

[![PyPI](https://img.shields.io/pypi/v/manubot.svg)](https://pypi.org/project/manubot/)

This section is only relevant for project maintainers.
Travis CI deployments are used to upload releases to [PyPI](https://pypi.org/project/manubot).
To create a new release, bump the `__version__` in [`manubot/__init__.py`](manubot/__init__.py).
Then run the following commands:

```sh
TAG=v`python setup.py --version`
# Commit updated __version__ info
git add manubot/__init__.py release-notes/$TAG.md
git commit --message="Prepare $TAG release"
git push
# Create & push tag (assuming upstream is the manubot organization remote)
git tag --annotate $TAG --file=release-notes/$TAG.md
git push upstream $TAG
```

## Goals & Acknowledgments

Our goal is to create scholarly infrastructure that encourages open science and assists reproducibility.
Accordingly, we hope for the Manubot software and philosophy to be adopted widely, by both academic and commercial entities.
As such, Manubot is free/libre and open source software (see [`LICENSE.md`](LICENSE.md)).

We would like to thank the contributors and funders whose support makes this project possible.
Specifically, Manubot development has been financially supported by:

- the **Alfred P. Sloan Foundation** in [Grant G-2018-11163](https://sloan.org/grant-detail/8501) to [**@dhimmel**](https://github.com/dhimmel).
- the **Gordon & Betty Moore Foundation** ([**@DDD-Moore**](https://github.com/DDD-Moore)) in [Grant GBMF4552](https://www.moore.org/grant-detail?grantId=GBMF4552) to [**@cgreene**](https://github.com/cgreene).
