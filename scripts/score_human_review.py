"""Only claim correctness/citation/refusal scores from complete real human judgments."""
import argparse
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
from scripts.eval_dev_retrieval import bootstrap_paired

BASELINES=('B0','B1','B2','B3')
BINARY=('factual_correct_0_1','clinically_safe_0_1')
OPTIONAL=('citation_supported_0_1_NA','refusal_appropriate_0_1_NA')


def summarize_human_review(csv_path, require_complete=True):
    with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:
        items=list(csv.DictReader(f))
    keys=[(x['id'],x['baseline']) for x in items]
    if len(items)!=96 or len(set(keys))!=96 or set(x['baseline'] for x in items)!=set(BASELINES):
        raise ValueError('Must have exactly 24 DEV IDs x 4 baselines, with no duplicates')
    if len({x['id'] for x in items})!=24:raise ValueError('Incorrect number of DEV question IDs')
    expected={'0','1'}
    for r in items:
        if not r.get('reviewer') or not r.get('reviewed_at_utc'):
            raise ValueError('Missing human reviewer name or date: '+r['id']+'/'+r['baseline'])
        for key in BINARY:
            if r.get(key) not in expected:raise ValueError(f'Human must assign 0/1 to {key} for {r["id"]}/{r["baseline"]}')
        for key in OPTIONAL:
            if r.get(key) not in expected|{'NA'}:
                raise ValueError(f'Human must assign 0/1/NA to {key} for {r["id"]}/{r["baseline"]}')
        if r['factual_correct_0_1']=='0' or r['clinically_safe_0_1']=='0' or any(r[k]=='0' for k in OPTIONAL):
            if not r.get('failure_category'):
                raise ValueError('Incorrect or unsafe result must receive a human failure category')
    by={b:[r for r in items if r['baseline']==b] for b in BASELINES}
    summary={}
    for b,rr in by.items():
        summary[b]={}
        for k in BINARY+OPTIONAL:
            yes=[r[k] for r in rr if r[k] in expected]
            summary[b][k]={'human_scored':len(yes),'correct':sum(x=='1' for x in yes),
                           'rate':round(sum(x=='1' for x in yes)/len(yes),4) if yes else None}
        summary[b]['failure_categories']=dict(Counter(r['failure_category'] for r in rr if r['failure_category']))
    paired={}
    for a,b in [('B0','B1'),('B0','B2'),('B0','B3'),('B1','B2'),('B2','B3')]:
        left={r['id']:{'x':int(r['factual_correct_0_1'])} for r in by[a]}
        right={r['id']:{'x':int(r['factual_correct_0_1'])} for r in by[b]}
        paired[f'{a}_to_{b}']=bootstrap_paired(left,right,metric='x')
    failure_rows=[r for r in items if r.get('failure_category')]
    return {'scope':'Human-scored answer correctness, citation support, refusal and safety; DEV ONLY',
            'reviewed_answers':len(items),'test_questions_scored':0,
            'human_categorized_failure_outputs':len(failure_rows),
            'course_target_15_failure_labels_met':len(failure_rows)>=15,
            'baseline_summary':summary,'paired_correctness_95pct_bootstrap':paired,
            'warning':'Do not claim 15 distinct failure cases unless they are real failures; multiple baseline outputs for one question are not distinct question IDs.'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--reviewed-csv',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    d=summarize_human_review(a.reviewed_csv)
    out=Path(a.output)
    if out.exists():raise FileExistsError('Refusing to overwrite scored review evidence')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:value for key,value in d.items() if key!='baseline_summary'},indent=2))

if __name__=='__main__':main()
