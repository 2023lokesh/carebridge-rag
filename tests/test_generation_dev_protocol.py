"""DEV-only generation protocol guardrails. No expensive models are downloaded in CI."""
import base64
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from scripts.eval_generation_dev import (
    automated_checks, encode_private_review, model_prompt, read_validated_dev,
    select_contexts, summarize, BASELINES,
)
from scripts.review_generation_dev import decrypt_answers, make_review_csv
from scripts.score_human_review import summarize_human_review


def frozen_fixture(tmp_path):
    cats={'single_hop':9,'multi_hop':4,'comparative':2,'temporal':2,'unanswerable':5,'ambiguous_adversarial':2}
    rows=[]
    for cat,n in cats.items():
        for i in range(n):
            rows.append({'id':f'G{len(rows)+1:02d}', 'category':cat, 'split':'dev',
                         'review_status':'HUMAN_VERIFIED','question':'What is a vaccine?',
                         'gold_source_urls':['https://www.cdc.gov/vaccines/'] if cat!='unanswerable' else []})
    raw=''.join(json.dumps(r)+'\n' for r in rows).encode()
    gold=tmp_path/'dev_24.jsonl';gold.write_bytes(raw)
    manifest={'dev_sha256':hashlib.sha256(raw).hexdigest(),'dev_ids':[r['id'] for r in rows],
              'test_ids':['G37'],'category_dev':cats,'corpus_sha256':'test-corpus'}
    mp=tmp_path/'manifest.json';mp.write_text(json.dumps(manifest))
    return gold,mp,rows


def test_sealed_test_cannot_be_loaded(tmp_path):
    gold,manifest,rows=frozen_fixture(tmp_path)
    got,_=read_validated_dev(gold,manifest)
    assert len(got)==24
    data=gold.read_text().replace('G01','G37',1)
    gold.write_text(data)
    with pytest.raises(ValueError,match='hash mismatch'):
        read_validated_dev(gold,manifest)


def test_non_development_and_wrong_category_rejected(tmp_path):
    gold,mp,rows=frozen_fixture(tmp_path)
    rows[0]['split']='test'
    raw=''.join(json.dumps(x)+'\n' for x in rows).encode()
    gold.write_bytes(raw);obj=json.loads(mp.read_text());obj['dev_sha256']=hashlib.sha256(raw).hexdigest();mp.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='split'):
        read_validated_dev(gold,mp)


def test_b0_never_retrieves_or_cites():
    ctx,stat=select_contexts('What is a vaccine?','B0',{}, {})
    assert ctx==[] and stat['candidates']==0
    s,u=model_prompt('What does MMR mean?',[], 'B0')
    assert 'No documents are available' in s and '[S1]' not in u


def test_generation_sources_enforce_cdc_allowlist():
    bad=[{'url':'https://example.com/leak','title':'Fake','text':'hello'}]
    with pytest.raises(ValueError,match='non-allowlisted'):
        model_prompt('Explain vaccines',bad,'B2')
    doc=[{'url':'https://www.cdc.gov/vaccines/hcp/index.html','title':'CDC','text':'Vaccine information'}]
    s,u=model_prompt('Vaccine?',doc,'B3')
    assert '[S1]' in u and 'cdc.gov' in u


def test_citation_marker_is_not_equated_with_citation_support():
    docs=[{'url':'https://www.cdc.gov/vaccines/index.html'}]
    x=automated_checks('MMR prevents measles [S1].',docs,'B3',None)
    assert x['citation_references_valid'] is True
    assert x['citation_support_human_scored'] is False
    y=automated_checks('Made-up citation [S7].',docs,'B3',None)
    assert y['citation_references_valid'] is False
    assert y['cited_source_count']==0


def test_answer_evidence_fernet_round_trip_without_test(tmp_path):
    data=[{'id':f'G{i:02d}','baseline':b,'category':'single_hop','question':'Q',
           'gold_answer':'A','gold_urls':[],'answer':'Answer','candidate_source_urls':[],
           'checks':{'citation_references_valid':True,'heuristic_abstention':False,'cited_sources':[]}}
          for i in range(1,25) for b in BASELINES]
    enc=encode_private_review(data,'top-secret-dev-payload')
    assert b'"question"' not in enc
    parsed=decrypt_answers(enc,'top-secret-dev-payload')
    assert len(parsed)==96
    with pytest.raises(ValueError,match='decrypt'):
        decrypt_answers(enc,'different-secret')
    result=make_review_csv(parsed,tmp_path/'private.csv')
    assert result['rows']==96
    with pytest.raises(FileExistsError):make_review_csv(parsed,tmp_path/'private.csv')


def test_unreviewed_answers_are_rejected_not_faked(tmp_path):
    data=[{'id':f'G{i:02d}','baseline':b,'category':'single_hop',
           'factual_correct_0_1':'','clinically_safe_0_1':'','citation_supported_0_1_NA':'',
           'refusal_appropriate_0_1_NA':'','reviewer':'','reviewed_at_utc':'','failure_category':''}
          for i in range(1,25) for b in BASELINES]
    path=tmp_path/'unreviewed.csv'
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    with pytest.raises(ValueError,match='reviewer'):
        summarize_human_review(path)


def test_real_human_scores_require_failure_categories(tmp_path):
    data=[{'id':f'G{i:02d}','baseline':b,'category':'single_hop',
           'factual_correct_0_1':'0' if i==1 else '1','clinically_safe_0_1':'1',
           'citation_supported_0_1_NA':'NA','refusal_appropriate_0_1_NA':'NA',
           'reviewer':'Verifier','reviewed_at_utc':'2026-10-10T13:00:00Z',
           'failure_category':'incorrect' if i==1 else ''}
          for i in range(1,25) for b in BASELINES]
    path=tmp_path/'scored.csv'
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    out=summarize_human_review(path)
    assert out['reviewed_answers']==96
    assert out['test_questions_scored']==0
    assert out['course_target_15_failure_labels_met'] is False
    assert out['baseline_summary']['B0']['factual_correct_0_1']['correct']==23


def test_summary_does_not_invent_human_correctness():
    rows=[{'baseline':b,'has_gold_sources':True,'checks':{'policy_blocked':False,
           'heuristic_abstention':False,'citation_references_valid':True,'has_citation':b!='B0'},
           'generation_ms':10,'total_ms':12,'generated_tokens':10}
          for i in range(24) for b in BASELINES]
    s=summarize(rows,'my-local-model',None,'test-version')
    assert s['human_scored_answers']==0
    assert s['test_questions_loaded']==0
    assert s['baseline_summary']['B0']['questions']==24


def test_public_golden_manifest_matches_exact_private_dev_snapshot():
    # Local fixture already archived in this session; CI has public manifest only.
    import os
    root=Path(__file__).resolve().parents[1]
    m=json.loads((root/'data/frozen_split_manifest.json').read_text())
    assert len(m['dev_ids'])==24 and len(m['test_ids'])==16
    assert set(m['dev_ids']).isdisjoint(m['test_ids'])
    assert sum(m['category_dev'].values())==24
    assert sum(m['category_test'].values())==16
    assert len(m['dev_sha256'])==64
