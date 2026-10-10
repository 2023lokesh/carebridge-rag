import json
import pytest
from scripts.dev_eval_report import report


def make_run(tmp_path,name,vals):
    rows=[{'id':str(i),'metrics':{k:val for k in ['recall_at_5','recall_at_20','mrr','ndcg_at_10']},
           **({'pre_rerank_metrics':{k:val-0.1 for k in ['recall_at_5','recall_at_20','mrr','ndcg_at_10']}} if name=='B3' else {})} for i,val in enumerate(vals)]
    p=tmp_path/(name+'.json')
    p.write_text(json.dumps({'summary':{'baseline':name},'per_question':rows}))
    return p


def test_report_paired_and_reranker_lift(tmp_path):
    a=make_run(tmp_path,'B1',[0.5]*18);b=make_run(tmp_path,'B2',[0.6]*18);c=make_run(tmp_path,'B3',[0.7]*18)
    result=report(a,b,c,tmp_path/'paired.json')
    assert result['test_items_scored']==0
    assert result['paired_95pct_bootstrap_CIs']['B1_to_B2']['recall_at_5']['mean_delta']==0.1
    assert result['one_factor_reranker_lift_vs_pre_crossencoder_RRF_candidates']['recall_at_5']['mean_delta']==0.1


def test_refuses_mismatched_questions(tmp_path):
    a=make_run(tmp_path,'B1',[.5]*18);b=make_run(tmp_path,'B2',[.5]*17);c=make_run(tmp_path,'B3',[.5]*18)
    with pytest.raises(ValueError,match='identical 18'):
        report(a,b,c,tmp_path/'paired.json')
