"""Decrypt DEV-only generated answers locally and prepare editable human-review CSV.

Never publish this CSV to the public repository or to unencrypted Actions artifacts.
"""
import argparse
import base64
import csv
import hashlib
import json
from pathlib import Path

FIELDS = [
    'id','category','baseline','question','gold_answer','gold_source_urls','answer',
    'selected_sources','cited_sources','auto_marker_valid','auto_refusal_guess',
    'factual_correct_0_1','citation_supported_0_1_NA','refusal_appropriate_0_1_NA',
    'clinically_safe_0_1','failure_category','reviewer','reviewed_at_utc','review_notes',
]


def decrypt_answers(encrypted_bytes, secret):
    from cryptography.fernet import Fernet, InvalidToken
    key=base64.urlsafe_b64encode(hashlib.sha256(('CareBridge-DEV-generation-review-v1:'+secret.strip()).encode('utf8')).digest())
    try:
        data=json.loads(Fernet(key).decrypt(encrypted_bytes))
    except (InvalidToken,ValueError) as exc:
        raise ValueError('Could not decrypt evidence; check the original DEV-only secret') from exc
    if len(data)!=96 or len({(r['id'],r['baseline']) for r in data})!=96:
        raise ValueError('Expected all 24 DEV IDs across four distinct baselines')
    if {r['baseline'] for r in data}!={'B0','B1','B2','B3'}:
        raise ValueError('Unexpected baseline in review artifact')
    return data


def make_review_csv(records,out):
    dest=Path(out)
    if dest.exists():raise FileExistsError('Refusing to overwrite a human-reviewed file')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=FIELDS)
        writer.writeheader()
        for r in records:
            checks=r['checks']
            writer.writerow({
                'id':r['id'],'category':r['category'],'baseline':r['baseline'],
                'question':r['question'],'gold_answer':r['gold_answer'],
                'gold_source_urls':'; '.join(r['gold_urls']),
                'answer':r['answer'],
                'selected_sources':'; '.join(r['candidate_source_urls']),
                'cited_sources':'; '.join(x['url'] for x in checks['cited_sources']),
                'auto_marker_valid':str(checks['citation_references_valid']),
                'auto_refusal_guess':str(checks['heuristic_abstention']),
            })
    return {'rows':len(records),'status':'human scoring NOT yet performed','local_private_csv':str(dest)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--secret-file',required=True,help='Existing DEV-only one-line base64 secret file; never commit')
    p.add_argument('--encrypted',required=True,help='PRIVATE_answer_review.json.fernet from Actions artifact')
    p.add_argument('--output',default='.private_eval/human_review.csv')
    a=p.parse_args()
    secret=Path(a.secret_file).read_text(encoding='utf8').strip()
    result=make_review_csv(decrypt_answers(Path(a.encrypted).read_bytes(),secret),a.output)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
