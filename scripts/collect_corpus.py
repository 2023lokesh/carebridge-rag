"""Execute crawl -> normalize -> independent inventory. No scores fabricated."""
import argparse
import json
from pathlib import Path
from carebridge.crawler import EthicalCrawler
from carebridge.extract import extract_manifest
from carebridge.audit import audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--contact',required=True)
    parser.add_argument('--max-pages',type=int,default=165)
    parser.add_argument('--raw-dir',default='data/raw')
    parser.add_argument('--normalized',default='data/normalized.jsonl')
    args=parser.parse_args()
    crawl=EthicalCrawler(args.contact,out=args.raw_dir).crawl(args.max_pages)
    if not (Path(args.raw_dir)/'manifest.jsonl').exists():
        raise SystemExit('Crawler produced no raw archive; no inventory to report.')
    extract=extract_manifest(str(Path(args.raw_dir)/'manifest.jsonl'),args.normalized)
    inventory=audit(str(Path(args.raw_dir)/'manifest.jsonl'),args.normalized,'reports/01_ingestion_metrics.json')
    print(json.dumps({'crawl':crawl,'extract':extract,'verified_inventory':inventory},indent=2))
    if not inventory['meets_assignment_minima']:
        raise SystemExit('Corpus requirements NOT met; inspect saved inventory before claiming completion.')

if __name__=='__main__':main()
