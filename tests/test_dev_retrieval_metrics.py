from scripts.eval_dev_retrieval import _metrics, bootstrap_paired


def test_gold_urls_count_once_even_when_many_chunks_match():
    gold=['https://www.cdc.gov/a','https://www.cdc.gov/b']
    docs=[{'url':gold[0]},{'url':gold[0]},{'url':'https://www.cdc.gov/miss'},{'url':gold[1]}]
    m=_metrics(gold,docs)
    assert m['recall_at_5']==1
    assert m['recall_at_20']==1
    assert m['mrr']==1
    assert 0<=m['ndcg_at_10']<=1


def test_paired_bootstrap_is_reproducible():
    a={'x':{'recall_at_5':0},'y':{'recall_at_5':.5}}
    b={'x':{'recall_at_5':.5},'y':{'recall_at_5':1}}
    res=bootstrap_paired(a,b)
    assert res['mean_delta']==.5
    assert res==bootstrap_paired(a,b)
