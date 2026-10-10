"""Paired DEV-only source-URL retrieval comparison, with explicit study limitations."""
import argparse
import json
from pathlib import Path
from scripts.eval_dev_retrieval import bootstrap_paired

METRICS=('recall_at_5','recall_at_20','mrr','ndcg_at_10')

def report(b1_path,b2_path,b3_path,output):
    runs={name:json.loads(Path(p).read_text(encoding='utf8'))
          for name,p in [('B1',b1_path),('B2',b2_path),('B3',b3_path)]}
    if any(run['summary']['baseline']!=name for name,run in runs.items()):
        raise ValueError('Baseline label mismatch')
    ids_by_run={name:{x['id'] for x in run['per_question']} for name,run in runs.items()}
    ids=ids_by_run['B1']
    if len(ids)!=18 or any(x!=ids for x in ids_by_run.values()):
        raise ValueError('All 3 baselines must score identical 18 source-labelled DEV questions')
    per={name:{x['id']:x['metrics'] for x in run['per_question']} for name,run in runs.items()}
    contrasts={}
    for a,b in [('B1','B2'),('B1','B3'),('B2','B3')]:
        contrasts[f'{a}_to_{b}']={m:bootstrap_paired(per[a],per[b],m) for m in METRICS}
    before={x['id']:x['pre_rerank_metrics'] for x in runs['B3']['per_question']
            if x.get('pre_rerank_metrics') is not None}
    if set(before)!=ids:
        raise ValueError('B3 must log its *identical 20 candidates* before cross-encoder reranking')
    reranker_lift={m:bootstrap_paired(before,per['B3'],m) for m in METRICS}
    data={
      'scope':'18 answerable/source-labelled DEV questions only; 16 TEST questions never loaded',
      'gold_origin':'AI-assisted question drafts, team-attested individual self-review',
      'metric_granularity':'source URL labels, not chunk-level judgments; no answer generation',
      'full_dev_items':24,'retrieval_scored_items':18,'test_items_scored':0,
      'baselines':{n:r['summary'] for n,r in runs.items()},
      'paired_95pct_bootstrap_CIs':contrasts,
      'one_factor_reranker_lift_vs_pre_crossencoder_RRF_candidates':reranker_lift,
      'interpretation':['Differences involving B3 change chunking/retrieval/reranking and are not one-factor causal estimates.',
                        'Only within-B3 pre/post reranking comparison isolates the cross-encoder.',
                        'Model cold-start, answer correctness, citation validity, refusals, and cost are NOT measured.',
                        'No development results should be presented as untouched test performance.']
    }
    dest=Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError('Do not overwrite a previous report')
    dest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
    return data


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--b1',required=True)
    p.add_argument('--b2',required=True)
    p.add_argument('--b3',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    x=report(a.b1,a.b2,a.b3,a.output)
    print(json.dumps({'scope':x['scope'],'aggregates':x['baselines'],
                      'reranker_lift':x['one_factor_reranker_lift_vs_pre_crossencoder_RRF_candidates']},indent=2))

if __name__=='__main__':main()
