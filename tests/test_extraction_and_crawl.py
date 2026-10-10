import hashlib
import json
from pathlib import Path
from carebridge.crawler import EthicalCrawler
from carebridge.extract import normalize_html,normalize_pdf,extract_manifest

def test_robots_fail_closed_and_descriptive_contact(tmp_path,monkeypatch):
    crawler=EthicalCrawler('reviewed-contact@example.org',out=tmp_path)
    assert 'reviewed-contact@example.org' in crawler.agent
    assert not crawler.permitted('https://www.cdc.gov/vaccines/hcp/current-vis/index.html')
    class FakeResp:
        def __init__(self,text):self.text=text
        def raise_for_status(self):pass
    monkeypatch.setattr(crawler.session,'get',lambda *a,**kw:FakeResp('User-agent: *\nDisallow: /vaccines/private/\n'))
    monkeypatch.setattr(crawler,'_throttle',lambda:None)
    crawler.load_robots()
    assert crawler.permitted('https://www.cdc.gov/vaccines/hcp/current-vis/index.html')
    assert not crawler.permitted('https://www.cdc.gov/vaccines/private/test.html')
    assert not crawler.permitted('https://other.example/vaccines/help')

def test_html_table_and_pdf_extraction(tmp_path):
    html=b'''<html><head><title>CDC demo schedule</title></head>
      <body><nav>unrelated navigation</nav><main><h1>Schedule</h1>
      <table><tr><th>Vaccine</th><th>Timing</th></tr>
      <tr><td>MMR</td><td>age dependent schedule information for review</td></tr></table>
      <p>Vaccination schedules are managed by clinicians using up-to-date guidance.</p>
      </main></body></html>'''
    title,blocks=normalize_html(html)
    assert title=='CDC demo schedule'
    assert any(b['is_table'] and 'MMR' in b['text'] and 'Vaccine' in b['text'] for b in blocks)
    assert all('unrelated navigation' not in b['text'] for b in blocks)
    import fitz
    doc=fitz.open();page=doc.new_page()
    page.insert_text((72,72),'COVID-19 vaccines can help prevent severe disease and hospitalization among patients.')
    pdf=doc.tobytes();doc.close()
    _,extracted=normalize_pdf(pdf)
    assert extracted and 'COVID-19' in extracted[0]['text']
    raw=tmp_path/'raw';raw.mkdir()
    entries=[]
    for idx,(content,mime,url) in enumerate([(html,'text/html','https://www.cdc.gov/vaccines/example/schedule.html'),
              (pdf,'application/pdf','https://www.cdc.gov/vaccines/example/vis.pdf')]):
        sha=hashlib.sha256(content).hexdigest();path=raw/f'{sha}.bin';path.write_bytes(content)
        entries.append({'source_url':url,'raw_path':str(path),'raw_sha256':sha,'mime_type':mime,'crawl_timestamp':'2026-10-09T21:00:00Z'})
    manifest=raw/'manifest.jsonl';manifest.write_text(''.join(json.dumps(e)+'\n' for e in entries))
    dest=tmp_path/'normalized.jsonl';r=extract_manifest(str(manifest),str(dest))
    results=[json.loads(x) for x in dest.read_text().splitlines()]
    assert r['raw_documents_unique']==2
    assert any(x['page_type']=='table' for x in results)
    assert any(x['page_type']=='pdf' for x in results)
