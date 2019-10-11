import copy
import pytest


from manubot.cite.csl_item import (
    csl_item_set_standard_id,
    CSL_Item)


class Test_CSL_Item:

    def test_constuctor_empty(self):
        assert CSL_Item() == {}

    def test_constuctor_non_empty(self):
        d = {'title': 'My book'}
        assert CSL_Item(d) == d
        
    def test_constuctor_by_keyword(self):
        assert CSL_Item(type='journal-article') == {'type': 'journal-article'}

    def test_constuctor_by_combination(self):
            assert CSL_Item({'title': 'My journal article'},
                            type='journal-article') == \
            {'title': 'My journal article', 'type': 'journal-article'}

    def test_fixtype_makes_change(self):
        assert CSL_Item(type='journal-article').fix_type() == {'type': 'article-journal'}

    def test_fixtype_makes_no_change1(self):    
        assert CSL_Item().fix_type() == {}

    def test_fixtype_makes_no_change2(self):            
        assert CSL_Item(type='book').fix_type() == {'type': 'book'}

    @pytest.mark.skip("Not implemented")
    def test_add_note_manubot_version_on_fixed_version(self):
        assert CSL_Item().add_note_manubot_version('1.1.1')['note'] == \
             'This CSL JSON Item was automatically generated by Manubot v1.1.1 using citation-by-identifier.'

    @pytest.mark.skip("Not implemented")
    def test_add_note_manubot_version(self):
        string = CSL_Item().add_note_manubot_version()['note']
        assert string.startswith('This CSL JSON Item')

    @pytest.mark.skip("Not implemented")
    def test_add_note_standard_id_and_note_dict(self):
         assert CSL_Item().add_note_standard_id('abc').note_dict() == \
            {'standard_id': 'abc'}




@pytest.mark.parametrize(
    ['csl_item', 'standard_citation'],
    [
        (
            {'id': 'my-id', 'standard_citation': 'doi:10.7554/elife.32822'},
            'doi:10.7554/elife.32822',
        ),
        (
            {'id': 'doi:10.7554/elife.32822'},
            'doi:10.7554/elife.32822',
        ),
        (
            {'id': 'doi:10.7554/ELIFE.32822'},
            'doi:10.7554/elife.32822',
        ),
        (
            {'id': 'my-id'},
            'raw:my-id',
        ),
    ],
    ids=[
        'from_standard_citation',
        'from_doi_id',
        'from_doi_id_standardize',
        'from_raw_id',
    ]
)
def test_csl_item_set_standard_id(csl_item, standard_citation):
    output = csl_item_set_standard_id(csl_item)
    assert output is csl_item
    assert output['id'] == standard_citation


def test_csl_item_set_standard_id_repeated():
    csl_item = {
        'id': 'pmid:1',
        'type': 'article-journal',
    }
    # csl_item_0 = copy.deepcopy(csl_item)
    csl_item_1 = copy.deepcopy(csl_item_set_standard_id(csl_item))
    assert 'standard_citation' not in 'csl_item'
    csl_item_2 = copy.deepcopy(csl_item_set_standard_id(csl_item))
    assert csl_item_1 == csl_item_2


def test_csl_item_set_standard_id_note():
    """
    Test extracting standard_id from a note and setting additional
    note fields.
    """
    csl_item = {
        'id': 'original-id',
        'type': 'article-journal',
        'note': 'standard_id: doi:10.1371/journal.PPAT.1006256',
    }
    csl_item_set_standard_id(csl_item)
    assert csl_item['id'] == 'doi:10.1371/journal.ppat.1006256'
    from manubot.cite.citeproc import parse_csl_item_note
    note_dict = parse_csl_item_note(csl_item['note'])
    assert note_dict['original_id'] == 'original-id'
    assert note_dict['original_standard_id'] == 'doi:10.1371/journal.PPAT.1006256'

