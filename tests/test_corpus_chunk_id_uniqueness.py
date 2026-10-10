from carebridge.corpus import chunk_documents,stable_id
def test_repeat_cdc_paragraphs_do_not_collide():
    url="https://www.cdc.gov/vaccines/hcp/current-vis/mmr.html"
    d={"url":url,"doc_id":stable_id(url),"title":"MMR","section":"One","page_type":"html","text":"Measles mumps and rubella"}
    for strategy in ("fixed","heading"):
        out=chunk_documents([d,d,{**d,"section":"Two"}],strategy)
        assert len(out)==2
        assert len({r["chunk_id"] for r in out})==2
