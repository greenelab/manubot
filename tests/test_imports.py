
def test_imports():
    import manubot.cite
    import manubot.cite.arxiv
    import manubot.cite.doi
    import manubot.cite.pubmed
    import manubot.cite.url
    import manubot.manuscript
    assert isinstance(manubot.cite.citeproc_retrievers, dict)
