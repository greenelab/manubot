import copy
import functools

import jsonref
import jsonschema

citeproc_type_fixer = {
    'journal-article': 'article-journal',
    'book-chapter': 'chapter',
    'posted-content': 'manuscript',
    'proceedings-article': 'paper-conference',
    'standard': 'entry',
    'reference-entry': 'entry',
}


def citeproc_passthrough(csl_item, set_id=None, prune=True):
    """
    Fix errors in a CSL item, according to the CSL JSON schema, and optionally
    change its id.

    http://docs.citationstyles.org/en/1.0.1/specification.html
    http://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    https://github.com/citation-style-language/schema/blob/master/csl-data.json
    """
    if set_id is not None:
        csl_item['id'] = set_id

    # Correct invalid CSL item types
    # See https://github.com/CrossRef/rest-api-doc/issues/187
    csl_item['type'] = citeproc_type_fixer.get(csl_item['type'], csl_item['type'])

    if prune:
        # Remove fields that violate the CSL Item JSON Schema
        validator = get_jsonschema_csl_validator()
        csl = [csl_item]
        errors = list(validator.iter_errors(csl))
        csl_item, = remove_jsonschema_errors(csl, errors)

    # Default CSL type to entry
    csl_item['type'] = csl_item.get('type', 'entry')

    if prune:
        # Confirm that corrected CSL validates
        validator.validate([csl_item])
    return csl_item


@functools.lru_cache()
def get_jsonschema_csl_validator():
    """
    Return a jsonschema validator for the CSL Item JSON Schema
    """
    url = 'https://github.com/citation-style-language/schema/raw/4846e02f0a775a8272819204379a4f8d7f45c16c/csl-data.json'
    # Use jsonref to workaround https://github.com/Julian/jsonschema/issues/447
    schema = jsonref.load_uri(url, jsonschema=True)
    # Cannot yet infer draft from schema https://github.com/citation-style-language/schema/pull/153
    jsonschema.Draft3Validator.check_schema(schema)
    return jsonschema.Draft3Validator(schema)


def remove_jsonschema_errors(instance, errors):
    """
    Remove fields that produced JSON Schema errors.
    https://github.com/Julian/jsonschema/issues/448
    """
    instance = copy.deepcopy(instance)
    errors = sorted(errors, key=lambda e: e.path, reverse=True)
    for error in errors:
        _remove_error(instance, error)
    return instance


def _delete_elem(instance, path):
    """
    Helper function for remove_jsonschema_errors
    """
    *head, tail = path
    for key in head:
        instance = instance[key]
    del instance[tail]


def _remove_error(instance, error):
    """
    Helper function for remove_jsonschema_errors
    """
    if error.validator == 'additionalProperties':
        extras = set(error.instance) - set(error.schema['properties'])
        for key in extras:
            _delete_elem(instance, path=list(error.path) + [key])
    elif error.validator in {'enum', 'type'}:
        _delete_elem(instance, error.path)
    else:
        raise NotImplementedError(f'{error.validator} is not yet supported')
