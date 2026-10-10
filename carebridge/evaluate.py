"""Honest evaluation utilities. Never reports invented or AI-unverified scores."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from .rag import answer, retrieve

CATEGORIES={"single_hop":15,"multi_hop":6,"comparative":4,"temporal":4,"unanswerable":8,"ambiguous_adversarial":3}
DEV_PER_CATEGORY={"single_hop":9,"multi_hop":4,"comparative":2,"temporal":2,"unanswerable":5,"ambiguous_adversarial":2}

def stratified_split(items,seed=633):
    groups=defaultdict(list)
    for row in items:groups[row["category"]].append(row)
    for cat,required in CATEGORIES.items():
        if len(groups[cat])<required:raise ValueError(f"Need >= {required} human-verified items for {cat}")
        if any(not row.get("human_verified_by") for row in groups[cat]):raise ValueError(f"Missing human verification: {cat}")
    rand=random.Random(seed);dev=[];test=[]
    for cat in CATEGORIES:
        group=list(groups[cat]);rand.shuffle(group)
        n=DEV_PER_CATEGORY[cat]
        dev.extend(group[:n]);test.extend(group[n:])
    return dev,test

def reciprocal_rank(gold_ids,retrieved):
    return next((1/i for i,r in enumerate(retrieved,1) if r["chunk_id"] in gold_ids),0.0)

def retrieval_metrics(items, mode="hybrid"):
    scores=[]
    for item in items:
        rows,_=retrieve(item["question"],mode,20)
        ids=set(item.get("gold_chunk_ids",[]))
        if not ids:continue
        ranks=[i for i,r in enumerate(rows,1) if r["chunk_id"] in ids]
        scores.append({"recall_5":len([i for i in ranks if i<=5])/len(ids),
            "recall_20":len([i for i in ranks if i<=20])/len(ids),
            "mrr":1/min(ranks) if ranks else 0,
            "ndcg_10":sum(1/__import__('math').log2(i+1) for i in ranks if i<=10)/sum(1/__import__('math').log2(i+1) for i in range(1,min(len(ids),10)+1))})
    return {"items":len(scores),**({key:round(sum(x[key] for x in scores)/len(scores),4) for key in scores[0]} if scores else {})}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--gold",required=True,help="JSONL: 40 independently human-verified items");p.add_argument("--split-out",default="data/eval_split.json")
    a=p.parse_args();items=[json.loads(x) for x in Path(a.gold).read_text().splitlines() if x.strip()]
    dev,test=stratified_split(items)
    Path(a.split_out).write_text(json.dumps({"dev":dev,"test":test},indent=2))
    print(f"Created stratified split: dev={len(dev)}, test={len(test)}. Test set NOT executed.")
