"""Auditable corpus inventory. Counts source documents, NOT extracted chunks.

Fail closed on missing raw files / changed hashes / missing normalization. A failed
threshold never becomes a positive result in a report.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

REQUIRED = {'unique_pages': 150, 'pdf_documents': 5, 'html_table_pages': 3}


def audit(manifest, normalized, output=None):
    manifest, normalized = Path(manifest), Path(normalized)
    records = [json.loads(x) for x in manifest.read_text(encoding='utf8').splitlines() if x.strip()]
    blocks = [json.loads(x) for x in normalized.read_text(encoding='utf8').splitlines() if x.strip()]
    by_url = {}
    errors = []
    for r in records:
        url = r['source_url']
        source = Path(r['raw_path'])
        if not source.is_absolute():
            # The crawler normally saves a path relative to the working directory.
            source = Path.cwd() / source
        if not source.is_file():
            errors.append(f'Missing raw bytes: {url}')
        elif hashlib.sha256(source.read_bytes()).hexdigest() != r['raw_sha256']:
            errors.append(f'Hash mismatch: {url}')
        if r.get('mime_type') not in ('text/html','application/pdf'):
            errors.append(f'Unexpected mime_type: {url}')
        by_url[url] = r
    normalized_urls = {b.get('source_url', b.get('url')) for b in blocks}
    unique_raw = set(by_url)
    pdf = {url for url,r in by_url.items() if r['mime_type'] == 'application/pdf' and url in normalized_urls}
    html_tables = {b.get('source_url',b.get('url')) for b in blocks if b.get('page_type') == 'table'
                   and b.get('source_url',b.get('url')) in unique_raw
                   and by_url[b.get('source_url',b.get('url'))]['mime_type'] == 'text/html'}
    # The 150 threshold counts distinct successful, normalized public URLs; not queue entries or chunks.
    count = len(unique_raw & normalized_urls)
    result = {'unique_pages':count, 'pdf_documents':len(pdf), 'html_table_pages':len(html_tables),
              'raw_urls':len(unique_raw),'normalized_blocks':len(blocks),'errors':errors,
              'thresholds':REQUIRED, 'meets_assignment_minima':False,
              'pdf_urls':sorted(pdf), 'table_urls':sorted(html_tables)}
    result['meets_assignment_minima'] = not errors and all(result[key]>=n for key,n in REQUIRED.items())
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,indent=2),encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',default='data/raw/manifest.jsonl')
    p.add_argument('--normalized',default='data/normalized.jsonl')
    p.add_argument('--output',default='reports/01_ingestion_metrics.json')
    p.add_argument('--require-thresholds',action='store_true')
    a=p.parse_args(); data=audit(a.manifest,a.normalized,a.output)
    print(json.dumps(data,indent=2))
    if a.require_thresholds and not data['meets_assignment_minima']:
        raise SystemExit('FAIL: dataset does not meet 150 pages / 5 PDFs / 3 table pages')
