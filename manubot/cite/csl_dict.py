from manubot.cite.citekey import standardize_citekey, infer_citekey_prefix, is_valid_citekey

def csl_item_set_standard_id(csl_item):
    """
    Extract the standard_id (standard citation key) for a csl_item and modify the csl_item in-place to set its "id" field.
    The standard_id is extracted from a "standard_citation" field, the "note" field, or the "id" field.
    If extracting the citation from the "id" field, uses the infer_citekey_prefix function to set the prefix.
    For example, if the extracted standard_id does not begin with a supported prefix (e.g. "doi:", "pmid:"
    or "raw:"), the citation is assumed to be raw and given a "raw:" prefix. The extracted citation
    (referred to as "original_standard_id") is checked for validity and standardized, after which it is
    the final "standard_id".

    Regarding csl_item modification, the csl_item "id" field is set to the standard_citation and the note field
    is created or updated with key-value pairs for standard_id, original_standard_id, and original_id.

    Note that the Manubot software generally refers to the "id" of a CSL Item as a citekey.
    However, in this context, we use "id" rather than "citekey" for consistency with CSL's "id" field.
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
        original_standard_id = infer_citekey_prefix(original_id)
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