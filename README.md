# The manuscript bot for automated scholarly publishing

[![Travis Linux Build Status](https://travis-ci.org/greenelab/manubot.svg?branch=master)](https://travis-ci.org/greenelab/manubot)
[![AppVeyor Windows Build Status](https://ci.appveyor.com/api/projects/status/u51tva6rmuk39xsc/branch/master?svg=true)](https://ci.appveyor.com/project/greenelab/manubot/branch/master)

The Manubot Python package prepares scholarly manuscripts for Pandoc consumption.
It automates and scripts several aspects of manuscript creation, including fetching bibliographic metadata for citations.

This program is designed to be used with clones of [Manubot Rootstock](https://github.com/greenelab/manubot-rootstock), which perform Pandoc conversion and continuous deployment.
See the Manubot Rootstock [usage guide](https://github.com/greenelab/manubot-rootstock/blob/master/USAGE.md) for more information.

## Usage

Installing the python package creates the `manubot` command line program.
This program is the primary interface to using Manubot.
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

See `manubot --help` for documentation of all command line arguments.

## Installation

Install the version specified by a git commit hash using:

```sh
COMMIT=33e512d21218263423de5f0d127aac4f8635468f
pip install git+https://github.com/greenelab/manubot@$COMMIT
```

Use the `--upgrade` argument to reinstall `manubot` with a different commit hash.

## Development

Create a development environment using:

```sh
conda create --name=manubot-dev python=3.6 jinja2 pandas pytest
conda activate manubot-dev  # assumes conda >= 4.4
pip install --editable .
```

Inside this environment, use `pytest` to run the test suite.
You can also use the `manubot` CLI to build manuscripts.
For example:

```sh
manubot build \
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
git add manubot/__init__.py
git commit --message="Set __version__ to $TAG"
git push
# Create & push tag (assuming upstream is greenelab remote)
git tag --annotate $TAG --message="Upgrade to $TAG"
git push upstream $TAG
```
