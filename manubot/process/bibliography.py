import json
import logging
import os
import pathlib

from manubot import __version__ as manubot_version
from manubot.cite.citekey import shorten_citekey
from manubot.util import read_serialized_data


def load_bibliography(path: str) -> list:
    """
    Load a bibliography as CSL Items (a CSL JSON Python object).
    For paths that already contain CSL Items (inferred from a .json or .yaml extension),
    parse these files directly. Otherwise, delegate conversion to CSL Items to pandoc-citeproc.
    """
    path_obj = pathlib.Path(path)
    if path_obj.suffix in {".json", ".yaml"}:
        try:
            csl_items = read_serialized_data(path)
        except Exception as error:
            logging.error(f"load_bibliography: error reading {path!r}.\n{error}")
            logging.info("load_bibliography exception info", exc_info=True)
            csl_items = []
    else:
        from manubot.pandoc.bibliography import (
            load_bibliography as load_bibliography_pandoc,
        )

        csl_items = load_bibliography_pandoc(path)
    if not isinstance(csl_items, list):
        logging.error(
            f"process.load_bibliography: csl_items read from {path} are of type {type(csl_items)}. "
            "Setting csl_items to an empty list."
        )
        csl_items = []
    from manubot.cite.csl_item import CSL_Item

    csl_items = [CSL_Item(csl_item) for csl_item in csl_items]
    return csl_items


def load_manual_references(paths=[], extra_csl_items=[]) -> dict:
    """
    Read manual references (overrides) from files specified by a list of paths.
    Returns a standard_citation to CSL Item dictionary. extra_csl_items specifies
    JSON CSL stored as a Python object, to be used in addition to the CSL JSON
    stored as text in the file specified by path. Set paths=[] to only use extra_csl_items.
    """
    from manubot.cite.csl_item import CSL_Item

    csl_items = []
    paths = list(dict.fromkeys(paths))  # remove duplicates
    for path in paths:
        path = os.fspath(path)
        path_obj = pathlib.Path(path)
        bibliography = load_bibliography(path)
        for csl_item in bibliography:
            csl_item.note_append_text(
                f"This CSL JSON Item was loaded by Manubot v{manubot_version} from a manual reference file."
            )
            csl_item.note_append_dict({"manual_reference_filename": path_obj.name})
            csl_items.append(csl_item)
    csl_items.extend(map(CSL_Item, extra_csl_items))
    manual_refs = dict()
    for csl_item in csl_items:
        try:
            csl_item.standardize_id()
        except Exception:
            csl_item_str = json.dumps(csl_item, indent=2)
            logging.info(
                f"Skipping csl_item where setting standard_id failed:\n{csl_item_str}",
                exc_info=True,
            )
            continue
        standard_id = csl_item["id"]
        csl_item.set_id(shorten_citekey(standard_id))
        csl_item.clean()
        manual_refs[standard_id] = csl_item
    return manual_refs
