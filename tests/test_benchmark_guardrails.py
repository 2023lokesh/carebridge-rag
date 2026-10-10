import json
import pytest
from carebridge.benchmark import check_ready,verify_item,metric_per_question,bootstrap_ci

def test_ai_practice_questions_not_accepted_as_gold():
    item={'id':'IDEA-001','category':'single_hop','human_verified_by':None,'review_status':'AI_SUGGESTION_NOT_GOLD'}
    with pytest.raises(ValueError,match='HUMAN_VERIFIED'):
        verify_item(item)

def test_human_verified_answer_needs_evidence_quote():
    item={'id':'TEST-001','category':'single_hop','human_verified_by':'Student','human_verified_at':'2026-10-09','review_status':'HUMAN_VERIFIED','gold_answer':'foo','gold_source_urls':['https://www.cdc.gov/vaccines/a']}
    with pytest.raises(ValueError,match='evidence quote'):
        verify_item(item)

def test_validity_metrics_and_paired_bootstrap():
    hits=[{'url':'https://www.cdc.gov/vaccines/a','chunk_id':'1'},{'url':'https://www.cdc.gov/vaccines/b','chunk_id':'2'}]
    m=metric_per_question(['https://www.cdc.gov/vaccines/b'],hits)
    assert m['recall_at_5']==1.0 and m['mrr']==0.5
    assert bootstrap_ci([.1,.2,.3])['mean_delta']==.2
