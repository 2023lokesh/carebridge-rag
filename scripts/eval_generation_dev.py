"""Private DEV-only B0-B3 text generation with a real, fixed local LLM.

This command deliberately does NOT score factual correctness, source entailment, or
refusal appropriateness. Those require independent human review of each answer.
Never publish questions, gold answers, or generated answer text in public artifacts.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import statistics
import time
from collections import Counter
from pathlib import Path

from carebridge.safety import screen_query, safe_url
from scripts.eval_dev_retrieval import bm25_rank, _dense_ranks, _load_neural, read_jsonl

BASELINES = ('B0', 'B1', 'B2', 'B3')
CITE_MARKER = re.compile(r'\[S([0-9]+)\]')
ABSTENTION = re.compile(
    r"\b(?:i (?:do not|don't) (?:have|know)|insufficient (?:information|evidence)|"
    r"cannot (?:answer|determine|verify|confirm|assess)|not enough (?:information|evidence)|"
    r"consult (?:a|your)|speak to (?:a|your)|please contact|cannot provide|"
    r"unable to (?:answer|determine))\b", re.I)


def read_validated_dev(path, manifest_path):
    """Fail closed unless the exact 24 frozen, SHA-attested DEV rows are supplied."""
    raw = Path(path).read_bytes()
    info = json.loads(Path(manifest_path).read_text(encoding='utf8'))
    if hashlib.sha256(raw).hexdigest() != info['dev_sha256']:
        raise ValueError('DEV hash mismatch; cannot run generation on an unapproved split')
    rows = [json.loads(line) for line in raw.decode('utf8').splitlines() if line.strip()]
    ids = {r['id'] for r in rows}
    if len(rows) != len(ids) or len(rows) != 24 or ids != set(info['dev_ids']):
        raise ValueError('DEV count/ids do not match the frozen manifest')
    if ids.intersection(info['test_ids']):
        raise ValueError('Sealed TEST contamination')
    if any(r.get('split') != 'dev' or r.get('review_status') != 'HUMAN_VERIFIED' for r in rows):
        raise ValueError('Unexpected split or missing team review attestation')
    required = Counter(info['category_dev'])
    if {k:sum(r['category']==k for r in rows) for k in required} != info['category_dev']:
        raise ValueError('Wrong DEV category distribution')
    return rows, info


def select_contexts(question, baseline, fixed, heading, top_k=5):
    """Retrieve with published B1/B2/B3 definitions; no test-set access."""
    if baseline == 'B0':
        return [], {'retrieval_ms':0.,'rerank_ms':0.,'candidates':0}
    start = time.perf_counter()
    if baseline == 'B1':
        docs = fixed['docs']
        ranks = bm25_rank(question, docs, 20)
        rank_ms = (time.perf_counter()-start)*1000
        return [docs[i] for i in ranks[:top_k]], {'retrieval_ms':round(rank_ms,3),'rerank_ms':0.,'candidates':len(ranks)}
    if baseline == 'B2':
        docs= fixed['docs']
        ranks=_dense_ranks(question,docs,fixed['coll'],fixed['model'],20)
        rank_ms=(time.perf_counter()-start)*1000
        return [docs[i] for i in ranks[:top_k]], {'retrieval_ms':round(rank_ms,3),'rerank_ms':0.,'candidates':len(ranks)}
    if baseline != 'B3':
        raise ValueError(f'Unknown baseline {baseline}')
    docs = heading['docs']
    bm=bm25_rank(question, docs, 20)
    dense=_dense_ranks(question,docs,heading['coll'],heading['model'],20)
    bmr={i:j for j,i in enumerate(bm,1)}
    dr={i:j for j,i in enumerate(dense,1)}
    candidates=set(bm)|set(dense)
    ranks=sorted(candidates,key=lambda i:(
        -(1/(60+bmr[i]) if i in bmr else 0)-(1/(60+dr[i]) if i in dr else 0), i))[:20]
    before_ce=(time.perf_counter()-start)*1000
    scores=heading['cross_encoder'].predict([[question, docs[i]['text']] for i in ranks])
    ranked=sorted(zip(ranks,scores),key=lambda v:-float(v[1]))
    total_ms=(time.perf_counter()-start)*1000
    return [docs[i] for i,_ in ranked[:top_k]], {
        'retrieval_ms':round(total_ms,3),'rerank_ms':round(total_ms-before_ce,3),'candidates':len(ranks)}


def model_prompt(question, documents, baseline):
    instruction=(
        'You are CareBridge, an educational assistant. Give a concise factual response. '
        'Never provide personal clinical decisions. When a question needs personal medical advice, refer to a clinician. '
        'When the available information cannot establish an answer, clearly say you lack sufficient information. '
        'Do not invent references.'
    )
    if baseline == 'B0':
        system=instruction + ' No documents are available. Answer using only your pretrained knowledge. Do not cite sources.'
        return system, f'Question: {question}\nAnswer:'
    sources=[]
    for i,d in enumerate(documents,1):
        url=d.get('url',d.get('source_url',''))
        if not safe_url(url):
            raise ValueError('Retrieval produced non-allowlisted CDC source URL')
        # Keep original source content unmodified except a bounded substring.
        snippet=' '.join(d['text'].split())[:850]
        sources.append(f'[S{i}] {d.get("title", "CDC source")}; URL: {url}\n{snippet}')
    system=(instruction+' Use ONLY the supplied CDC excerpts. Cite supported facts with [S1] etc. '
             'Do not cite a source marker that is not supplied. If excerpts do not answer the question, abstain.')
    user=f'CDC excerpts:\n'+ '\n\n'.join(sources) + f'\n\nQuestion: {question}\nAnswer:'
    return system, user


class SmallLocalGenerator:
    """Same actual autoregressive language model for B0, B1, B2, and B3."""
    def __init__(self, name, max_tokens=96):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch=torch
        self.transformers_version=transformers.__version__
        self.name=name
        self.max_tokens=max_tokens
        torch.set_num_threads(min(4,os.cpu_count() or 2))
        self.tokenizer=AutoTokenizer.from_pretrained(name)
        self.model=AutoModelForCausalLM.from_pretrained(name).eval().to('cpu')
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token=self.tokenizer.eos_token

    def generate(self, question, docs, baseline):
        system,user=model_prompt(question,docs,baseline)
        messages=[{'role':'system','content':system},{'role':'user','content':user}]
        prepared=self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        batch=self.tokenizer(prepared,return_tensors='pt',truncation=False)
        if batch['input_ids'].shape[-1] > 3500:
            raise ValueError('Prompts exceed the configured reproducible input budget')
        started=time.perf_counter()
        with self.torch.inference_mode():
            out=self.model.generate(**batch,do_sample=False,max_new_tokens=self.max_tokens,
                                    pad_token_id=self.tokenizer.pad_token_id)
        ms=(time.perf_counter()-started)*1000
        tokens=out[0][batch['input_ids'].shape[-1]:]
        return self.tokenizer.decode(tokens,skip_special_tokens=True).strip(), round(ms,2), int(len(tokens))


def automated_checks(answer, docs, baseline, policy_blocked):
    markers=CITE_MARKER.findall(answer)
    cited=[int(x) for x in markers]
    citations=[{'marker':f'S{i}','url':docs[i-1].get('url',docs[i-1].get('source_url'))} for i in sorted(set(cited)) if 1<=i<=len(docs)]
    return {
        'policy_blocked':bool(policy_blocked),
        'heuristic_abstention':bool(policy_blocked or ABSTENTION.search(answer)),
        'citation_markers':len(markers),
        'citation_references_valid':all(1<=i<=len(docs) for i in cited),
        'cited_source_count':len(citations),
        'cited_sources':citations,
        'has_citation':bool(citations),
        'answer_chars':len(answer),
        # A valid marker/URL is NOT proof the factual statement is entailed by a source.
        'citation_support_human_scored':False,
        'factual_correctness_human_scored':False,
        'refusal_appropriateness_human_scored':False,
    }


def summarize(rows, model_name, model_revision, version):
    by_model={}
    for name in BASELINES:
        selected=[r for r in rows if r['baseline']==name]
        gen_ms=sorted(r['generation_ms'] for r in selected)
        latency=sorted(r['total_ms'] for r in selected)
        flags=[r['checks'] for r in selected]
        by_model[name]={
            'questions':len(selected),'source_labelled':sum(bool(r['has_gold_sources']) for r in selected),
            'unanswerable_or_ambiguous_without_sources':sum(not r['has_gold_sources'] for r in selected),
            'policy_blocked':sum(r['checks']['policy_blocked'] for r in selected),
            'heuristic_abstentions':sum(r['checks']['heuristic_abstention'] for r in selected),
            'invalid_citation_references':sum(not r['checks']['citation_references_valid'] for r in selected),
            'outputs_with_valid_markers':sum(r['checks']['has_citation'] for r in selected),
            'p50_total_ms':round(statistics.median(latency),2),
            'p95_total_ms':round(latency[min(len(latency)-1,int(len(latency)*.95+.99999)-1)],2),
            'p50_generation_ms':round(statistics.median(gen_ms),2),
            'generated_tokens':sum(r['generated_tokens'] for r in selected),
            'quality_judgments':'PENDING HUMAN ADJUDICATION',
        }
    return {'evaluation':'DEV-only generated answers; automated checks NOT correctness scores',
            'generator_model':model_name,'model_revision':model_revision,
            'transformers_version':version,'decoding':'CPU, greedy, max_new_tokens=96',
            'full_dev_questions':24,'test_questions_loaded':0,'human_scored_answers':0,
            'baseline_summary':by_model,
            'limitations':['This includes the 6 questions previously excluded from retrieval scoring.',
                           'Heuristic abstention is not a clinically validated refusal metric.',
                           'Citation reference validity does not imply claim support.',
                           'Same small language model is used for all four baselines.',
                           'DEV results cannot be used as held-out test performance.']}


def encode_private_review(payload, secret):
    """Fernet-encrypt raw evaluation answers, derived from already configured DEV secret.

    Protects questions/answers from casual exposure in public Actions artifacts;
    does not protect if the DEV secret is disclosed. No TEST items are present.
    """
    from cryptography.fernet import Fernet
    material=hashlib.sha256(('CareBridge-DEV-generation-review-v1:'+secret.strip()).encode('utf8')).digest()
    key=base64.urlsafe_b64encode(material)
    return Fernet(key).encrypt(json.dumps(payload,ensure_ascii=False).encode('utf8'))


def run(dev,manifest,fixed_dir,heading_dir,output_dir,model_name,secret,max_new_tokens):
    rows,freeze=read_validated_dev(dev,manifest)
    fixed_info,fixed_docs,fixed_coll,fixed_model=_load_neural(fixed_dir)
    heading_info,heading_docs,heading_coll,heading_model=_load_neural(heading_dir)
    if fixed_info['strategy']!='fixed' or heading_info['strategy']!='heading':
        raise ValueError('Wrong fixed/heading Chroma index ordering')
    if fixed_info['corpus_sha256']!=heading_info['corpus_sha256'] or fixed_info['corpus_sha256']!=freeze['corpus_sha256']:
        raise ValueError('Incompatible corpus vs frozen development gold')
    from sentence_transformers import CrossEncoder
    fixed={'docs':fixed_docs,'coll':fixed_coll,'model':fixed_model}
    heading={'docs':heading_docs,'coll':heading_coll,'model':heading_model,
             'cross_encoder':CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')}
    generator=SmallLocalGenerator(model_name,max_new_tokens)
    output=[]
    # Interleave baselines per question for paired comparisons under similar runner conditions.
    for row in rows:
        q=row['question']
        common=screen_query(q)  # Apply identical deterministic safety policy to every baseline.
        for baseline in BASELINES:
            docs,stats=select_contexts(q,baseline,fixed,heading)
            if common:
                answer,gen_ms,ntokens=common,0.,0
            else:
                answer,gen_ms,ntokens=generator.generate(q,docs,baseline)
            checks=automated_checks(answer,docs,baseline,common)
            output.append({
                'id':row['id'],'category':row['category'],'baseline':baseline,'question':q,
                'gold_answer':row.get('gold_answer'),'gold_urls':row.get('gold_source_urls',[]),
                'answer':answer,'candidate_source_urls':[x['url'] for x in docs],
                'checks':checks,'retrieval_ms':stats['retrieval_ms'],'rerank_ms':stats['rerank_ms'],
                'generation_ms':gen_ms,'total_ms':round(stats['retrieval_ms']+gen_ms,2),
                'generated_tokens':ntokens,
                'has_gold_sources':bool(row.get('gold_source_urls')),
            })
        print(json.dumps({'processed_question_id':row['id'],'baselines_done':4}),flush=True)
    public={k:v for k,v in summarize(output,model_name,getattr(generator.model.config,'_commit_hash',None),generator.transformers_version).items()}
    public['freeze_sha256']=freeze['dev_sha256']
    public['index_sha256']=fixed_info['corpus_sha256']
    public['automated_per_id']=[{'id':r['id'],'baseline':r['baseline'],'category':r['category'],
                                'checks':{key:v for key,v in r['checks'].items() if key not in ('cited_sources',)},
                                'total_ms':r['total_ms'],'generation_ms':r['generation_ms']}
                               for r in output]
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=False)
    (out/'aggregate_automated.json').write_text(json.dumps(public,indent=2)+'\n',encoding='utf8')
    (out/'PRIVATE_answer_review.json.fernet').write_bytes(encode_private_review(output,secret))
    return {k:v for k,v in public.items() if k!='automated_per_id'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dev',default='.private_eval/dev_24.jsonl')
    p.add_argument('--manifest',default='data/frozen_split_manifest.json')
    p.add_argument('--fixed',default='data/chroma_fixed_v2')
    p.add_argument('--heading',default='data/chroma_heading_v2')
    p.add_argument('--output-dir',default='reports/generation_eval')
    p.add_argument('--model',default='HuggingFaceTB/SmolLM2-360M-Instruct')
    p.add_argument('--max-new-tokens',type=int,default=96)
    args=p.parse_args()
    if args.max_new_tokens!=96:
        raise ValueError('Use the preregistered max 96 tokens for all baselines')
    secret=os.environ.get('CAREBRIDGE_DEV_GOLD_GZIP_B64')
    if not secret:raise ValueError('Dev-only secret required for private answer encryption')
    print(json.dumps(run(args.dev,args.manifest,args.fixed,args.heading,args.output_dir,args.model,secret,args.max_new_tokens),indent=2))

if __name__=='__main__':main()
