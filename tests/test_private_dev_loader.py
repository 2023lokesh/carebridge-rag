import base64
import gzip
import hashlib
import json
from pathlib import Path
import pytest
from scripts.load_private_dev import load_from_secret


def fixture(tmp_path):
    rows=[{'id':f'G{i:02d}','category':'single_hop','split':'dev','review_status':'HUMAN_VERIFIED','gold_source_urls':['https://www.cdc.gov/vaccines/']} for i in range(1,25)]
    data=''.join(json.dumps(r)+'\n' for r in rows).encode()
    manifest={'dev_sha256':hashlib.sha256(data).hexdigest(),'dev_ids':[x['id'] for x in rows],
              'test_ids':['G25'],'counts_by_category':{'single_hop':{'dev':24}}}
    mp=tmp_path/'manifest.json';mp.write_text(json.dumps(manifest))
    secret=base64.b64encode(gzip.compress(data)).decode()
    return mp,secret,rows


def test_payload_hash_and_ids_verified(tmp_path):
    manifest,secret,rows=fixture(tmp_path)
    report=load_from_secret(secret,manifest,tmp_path/'private'/'dev.jsonl')
    assert report['dev_items']==24 and report['test_questions_loaded']==0
    assert (tmp_path/'private'/'dev.jsonl').is_file()


def test_tampered_dev_payload_rejected(tmp_path):
    manifest,secret,rows=fixture(tmp_path)
    raw=gzip.decompress(base64.b64decode(secret)).replace(b'G01',b'G99',1)
    bad=base64.b64encode(gzip.compress(raw)).decode()
    with pytest.raises(ValueError,match='SHA-256'):
        load_from_secret(bad,manifest,tmp_path/'dev.jsonl')
    assert not (tmp_path/'dev.jsonl').exists()


def test_secret_required(tmp_path):
    manifest,*_=fixture(tmp_path)
    with pytest.raises(ValueError,match='Actions secret'):
        load_from_secret('',manifest,tmp_path/'dev.jsonl')
