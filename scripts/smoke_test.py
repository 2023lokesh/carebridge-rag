"""HTTP smoke test for a *running* local or deployed CareBridge service.

Usage: python scripts/smoke_test.py --url http://127.0.0.1:8000
"""
import argparse
import json
from urllib.request import Request, urlopen

def run(url):
    url = url.rstrip('/')
    with urlopen(url + '/healthz', timeout=20) as response:
        health = json.loads(response.read().decode())
    assert health['status'] == 'ok', health
    payload = json.dumps({'question':'What does MMR protect against?','mode':'hybrid'}).encode()
    req = Request(url + '/api/chat', data=payload, headers={'Content-Type':'application/json'}, method='POST')
    with urlopen(req, timeout=30) as response:
        chat = json.loads(response.read().decode())
    assert not chat['refused'], chat
    assert 'measles' in chat['answer'].lower(), chat
    assert chat['sources'] and all(x['url'].startswith('https://www.cdc.gov/') for x in chat['sources']), chat
    print('PASS — service up, evidence-backed MMR answer, clickable CDC sources returned')
    print('health:', health)
    print('sources:', len(chat['sources']), 'candidates:', len(chat['trace']))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--url', default='http://127.0.0.1:8000')
    args = p.parse_args()
    run(args.url)
