"""Decode DEV-only frozen gold from a GitHub Actions secret; never print item text."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
from collections import Counter


def load_from_secret(value, manifest_path, output):
    info=json.loads(Path(manifest_path).read_text(encoding='utf8'))
    if not value:
        raise ValueError('Set the CAREBRIDGE_DEV_GOLD_GZIP_B64 repository Actions secret first')
    try:
        compressed=base64.b64decode(value.strip(),validate=True)
        if len(compressed)>50_000:
            raise ValueError('Dev payload is unexpectedly large')
        raw=gzip.decompress(compressed)
    except (ValueError, OSError) as e:
        raise ValueError('Could not decode approved development payload') from e
    if len(raw)>250_000:
        raise ValueError('Decompressed dev payload exceeds safety limit')
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=info['dev_sha256']:
        raise ValueError('Dev payload SHA-256 does not match the published frozen manifest')
    rows=[json.loads(x) for x in raw.decode('utf8').splitlines() if x.strip()]
    got={x['id'] for x in rows}
    assert len(rows)==24 and len(got)==24 and got==set(info['dev_ids']), 'Invalid DEV IDs'
    assert not (got & set(info['test_ids'])), 'Holdout contamination detected'
    assert all(x['split']=='dev' and x['review_status']=='HUMAN_VERIFIED' for x in rows)
    expected={cat:counts['dev'] for cat,counts in info['counts_by_category'].items()}
    assert Counter(x['category'] for x in rows)==Counter(expected), 'Category mismatch'
    dest=Path(output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(raw)
    dest.chmod(0o600)
    return {'dev_items':len(rows),'source_labelled':sum(bool(r.get('gold_source_urls')) for r in rows),
            'snapshot_sha256':digest, 'test_questions_loaded':0, 'verified':True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',default='data/frozen_split_manifest.json')
    p.add_argument('--output',default='.private_eval/dev_24.jsonl')
    args=p.parse_args()
    print(json.dumps(load_from_secret(os.environ.get('CAREBRIDGE_DEV_GOLD_GZIP_B64'),args.manifest,args.output),indent=2))

if __name__=='__main__':main()
