import functools
import logging
import re

from manubot.util import import_function

citeproc_retrievers = {
    'doi': 'manubot.cite.doi.get_doi_citeproc',
    'pmid': 'manubot.cite.pubmed.get_pubmed_citeproc',
    'pmcid': 'manubot.cite.pubmed.get_pmc_citeproc',
    'arxiv': 'manubot.cite.arxiv.get_arxiv_citeproc',
    'isbn': 'manubot.cite.isbn.get_isbn_citeproc',
    'wikidata': 'manubot.cite.wikidata.get_wikidata_citeproc',
    'url': 'manubot.cite.url.get_url_citeproc',
}

"""
Regex to extract citations.
The leading '@' is omitted from the single match group.

Same rules as pandoc, except more permissive in the following ways:

1. the final character can be a slash because many URLs end in a slash.
2. underscores are allowed in internal characters because URLs, DOIs, and
   citation tags often contain underscores.

If a citation string does not match this regex, it can be substituted for a
tag that does, as defined in citation-tags.tsv.

https://github.com/greenelab/manubot-rootstock/issues/2#issuecomment-312153192

Prototyped at https://regex101.com/r/s3Asz3/4
"""
citation_pattern = re.compile(
    r'(?<!\w)@([a-zA-Z0-9][\w:.#$%&\-+?<>~/]*[a-zA-Z0-9/])')


@functools.lru_cache(maxsize=5_000)
def standardize_citekey(citation, warn_if_changed=False):
    """
    Standardize citation identifiers based on their source
    """
    source, identifier = citation.split(':', 1)

    if source == 'doi':
        if identifier.startswith('10/'):
            from manubot.cite.doi import expand_short_doi
            try:
                identifier = expand_short_doi(identifier)
            except Exception as error:
                # If DOI shortening fails, return the unshortened DOI.
                # DOI metadata lookup will eventually fail somewhere with
                # appropriate error handling, as opposed to here.
                logging.error(
                    f'Error in expand_short_doi for {identifier} '
                    f'due to a {error.__class__.__name__}:\n{error}'
                )
                logging.info(error, exc_info=True)
        identifier = identifier.lower()

    if source == 'isbn':
        from isbnlib import to_isbn13
        identifier = to_isbn13(identifier)

    standard_citation = f'{source}:{identifier}'
    if warn_if_changed and citation != standard_citation:
        logging.warning(
            f'standardize_citekey expected citation to already be standardized.\n'
            f'Instead citation was changed from {citation} to {standard_citation}'
        )
    return standard_citation


regexes = {
    'pmid': re.compile(r'[1-9][0-9]{0,7}'),
    'pmcid': re.compile(r'PMC[0-9]+'),
    'doi': re.compile(r'10\.[0-9]{4,9}/\S+'),
    'shortdoi': re.compile(r'10/[a-zA-Z0-9]+'),
    'wikidata': re.compile(r'Q[0-9]+'),
}


def inspect_citekey(citation):
    """
    Check citekeys adhere to expected formats. If an issue is detected a
    string describing the issue is returned. Otherwise returns None.
    """
    source, identifier = citation.split(':', 1)

    if source == 'pmid':
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmid
        if identifier.startswith('PMC'):
            return (
                'PubMed Identifiers should start with digits rather than PMC. '
                f'Should {citation} switch the citation source to `pmcid`?'
            )
        elif not regexes['pmid'].fullmatch(identifier):
            return 'PubMed Identifiers should be 1-8 digits with no leading zeros.'

    if source == 'pmcid':
        # https://www.nlm.nih.gov/bsd/mms/medlineelements.html#pmc
        if not identifier.startswith('PMC'):
            return 'PubMed Central Identifiers must start with `PMC`.'
        elif not regexes['pmcid'].fullmatch(identifier):
            return (
                'Identifier does not conform to the PMCID regex. '
                'Double check the PMCID.'
            )

    if source == 'doi':
        if identifier.startswith('10.'):
            # https://www.crossref.org/blog/dois-and-matching-regular-expressions/
            if not regexes['doi'].fullmatch(identifier):
                return (
                    'Identifier does not conform to the DOI regex. '
                    'Double check the DOI.'
                )
        elif identifier.startswith('10/'):
            # shortDOI, see http://shortdoi.org
            if not regexes['shortdoi'].fullmatch(identifier):
                return (
                    'Identifier does not conform to the shortDOI regex. '
                    'Double check the shortDOI.'
                )
        else:
            return (
                'DOIs must start with `10.` (or `10/` for shortDOIs).'
            )

    if source == 'isbn':
        import isbnlib
        fail = isbnlib.notisbn(identifier, level='strict')
        if fail:
            return (
                f'identifier violates the ISBN syntax according to isbnlib v{isbnlib.__version__}'
            )

    if source == 'wikidata':
        # https://www.wikidata.org/wiki/Wikidata:Identifiers
        if not identifier.startswith('Q'):
            return (
                'Wikidata item IDs must start with `Q`.'
            )
        elif not regexes['wikidata'].fullmatch(identifier):
            return (
                'Identifier does not conform to the Wikidata regex. '
                'Double check the entity ID.'
            )

    return None


def is_valid_citekey(
        citekey, allow_tag=False, allow_raw=False, allow_pandoc_xnos=False):
    """
    Return True if citekey is a properly formatted string. Return False if
    citekey is not a citation or is an invalid citation.

    In the case citekey is invalid, an error is logged. This
    function does not catch all invalid citekeys, but instead performs cursory
    checks, such as ensuring citekeys adhere to the expected formats. No calls to
    external resources are used by these checks, so they will not detect
    citekeys to non-existent identifiers unless those identifiers violate
    their source's syntax.

    allow_tag=False, allow_raw=False, and allow_pandoc_xnos=False enable
    allowing citekey sources that are valid for Manubot manuscripts, but
    likely not elsewhere. allow_tag=True enables citekey tags (e.g.
    tag:citation-tag). allow_raw=True enables raw citekeys (e.g.
    raw:manual-reference). allow_pandoc_xnos=True still returns False for
    pandoc-xnos references (e.g. fig:figure-id), but does not log an error.
    With the default of False for these arguments, valid sources are restricted
    to those for which manubot can retrieve metadata based only on the
    standalone citekey.
    """
    if not isinstance(citekey, str):
        logging.error(
            f"citekey should be type 'str' not "
            f"{type(citekey).__name__!r}: {citekey!r}"
        )
        return False
    if citekey.startswith('@'):
        logging.error(f"invalid citekey: {citekey!r}\nstarts with '@'")
        return False
    try:
        source, identifier = citekey.split(':', 1)
    except ValueError:
        logging.error(
            f'citekey not splittable via a single colon: {citekey}. '
            'Citekeys must be in the format of `source:identifier`.'
        )
        return False

    if not source or not identifier:
        msg = f'invalid citekey: {citekey!r}\nblank source or identifier'
        logging.error(msg)
        return False

    if allow_pandoc_xnos:
        # Exempted non-citation sources used for pandoc-fignos,
        # pandoc-tablenos, and pandoc-eqnos
        pandoc_xnos_keys = {'fig', 'tbl', 'eq'}
        if source in pandoc_xnos_keys:
            return False
        if source.lower() in pandoc_xnos_keys:
            logging.error(
                f'pandoc-xnos reference types should be all lowercase.\n'
                f'Should {citekey!r} use {source.lower()!r} rather than "{source!r}"?'
            )
            return False

    # Check supported source type
    sources = set(citeproc_retrievers)
    if allow_raw:
        sources.add('raw')
    if allow_tag:
        sources.add('tag')
    if source not in sources:
        if source.lower() in sources:
            logging.error(
                f'citekey sources should be all lowercase.\n'
                f'Should {citekey} use "{source.lower()}" rather than "{source}"?'
            )
        else:
            logging.error(
                f'invalid citekey: {citekey!r}\n'
                f'Source {source!r} is not valid.\n'
                f'Valid citation sources are {{{", ".join(sorted(sources))}}}'
            )
        return False

    inspection = inspect_citekey(citekey)
    if inspection:
        logging.error(f'invalid {source} citekey: {citekey}\n{inspection}')
        return False

    return True


def shorten_citekey(citekey):
    """
    Return a shortened citekey derived from the input citekey.
    The input citekey should be standardized prior to this function,
    since differences in the input citekey will result in different shortened citekeys.
    Short citekeys are generated by converting the input citekey to a 6 byte hash,
    and then converting this digest to a base62 ASCII str. Shortened
    citekeys consist of characters in the following ranges: 0-9, a-z and A-Z.
    """
    import hashlib
    import base62
    assert '@' not in citekey
    as_bytes = citekey.encode()
    blake_hash = hashlib.blake2b(as_bytes, digest_size=6)
    digest = blake_hash.digest()
    short_citekey = base62.encodebytes(digest)
    return short_citekey


def citation_to_citeproc(citation, prune=True):
    """
    Return a dictionary with citation metadata
    """
    citation == standardize_citekey(citation, warn_if_changed=True)
    source, identifier = citation.split(':', 1)

    if source in citeproc_retrievers:
        citeproc_retriever = import_function(citeproc_retrievers[source])
        csl_item = citeproc_retriever(identifier)
    else:
        msg = f'Unsupported citation source {source} in {citation}'
        raise ValueError(msg)

    from manubot import __version__ as manubot_version
    from manubot.cite.citeproc import (
        citeproc_passthrough,
        append_to_csl_item_note,
    )

    note_text = f'This CSL JSON Item was automatically generated by Manubot v{manubot_version} using citation-by-identifier.'
    note_dict = {
        'standard_id': citation,
    }
    append_to_csl_item_note(csl_item, note_text, note_dict)

    short_citekey = shorten_citekey(citation)
    csl_item = citeproc_passthrough(csl_item, set_id=short_citekey, prune=prune)

    return csl_item


def infer_citation_prefix(citation):
    """
    Passthrough citation if it has a valid citation prefix. Otherwise,
    if the lowercase citation prefix is valid, convert the prefix to lowercase.
    Otherwise, assume citation is raw and prepend "raw:".
    """
    prefixes = [f'{x}:' for x in list(citeproc_retrievers) + ['raw']]
    for prefix in prefixes:
        if citation.startswith(prefix):
            return citation
        if citation.lower().startswith(prefix):
            return prefix + citation[len(prefix):]
    return f'raw:{citation}'


def csl_item_set_standard_id(csl_item):
    """
    Extract the standard_id (standard citation key) for a csl_item and modify the csl_item in-place to set its standard_id.
    The standard_id is extracted from a "standard_citation" field, the "note" field, or the "id" field.
    If extracting the citation from the "id" field, use the infer_citation_prefix function to set the prefix.
    For example, if the extracted standard_id does not begin with a supported prefix (e.g. "doi:", "pmid:"
    or "raw:"), the citation is assumed to be raw and given a "raw:" prefix. The extracted citation
    (referred to as "original_standard_id") is checked for validity and standardized, after which it is
    the final "standard_id".

    Regarding csl_item modification, the csl_item "id" field is set to the standard_citation and the note field
    is created or updated with key-value pairs for standard_citation, original_standard_citation, and original_id.
    """
    if not isinstance(csl_item, dict):
        raise ValueError("csl_item must be a CSL Data Item represented as a Python dictionary")

    from manubot.cite.citeproc import (
        append_to_csl_item_note,
        parse_csl_item_note,
    )
    note_dict = parse_csl_item_note(csl_item.get('note', ''))

    original_id = None
    original_standard_id = None
    if 'id' in csl_item:
        original_id = csl_item['id']
        original_standard_id = infer_citation_prefix(original_id)
    if 'standard_id' in note_dict:
        original_standard_id = note_dict['standard_id']
    if 'standard_citation' in csl_item:
        original_standard_id = csl_item.pop('standard_citation')
    if original_standard_id is None:
        raise ValueError(
            'csl_item_set_standard_id could not detect a field with a citation / standard_citation. '
            'Consider setting the CSL Item "id" field.'
        )
    assert is_valid_citekey(original_standard_id, allow_raw=True)
    standard_id = standardize_citekey(original_standard_id, warn_if_changed=False)
    add_to_note = {}
    if original_id and original_id != standard_id:
        if original_id != note_dict.get('original_id'):
            add_to_note['original_id'] = original_id
    if original_standard_id and original_standard_id != standard_id:
        if original_standard_id != note_dict.get('original_standard_id'):
            add_to_note['original_standard_id'] = original_standard_id
    if standard_id != note_dict.get('standard_id'):
        add_to_note['standard_id'] = standard_id
    append_to_csl_item_note(csl_item, dictionary=add_to_note)
    csl_item['id'] = standard_id
    return csl_item
