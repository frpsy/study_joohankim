"""강의 구조·근거 연결 검사. 내용의 정확성과 설명의 충분성은 별도 대조 검수가 필요하다.

실행: python scripts/validate_study_pages.py
회귀 검사: python -m unittest discover -s tests -p 'test_study_validation.py'
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from collections import Counter
import json,sys,re

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.images=[];self.links=[];self.units={};self.active=None;self.depth=0;self.level=0;self.details=0;self.errors=[];self.role=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag=='img':self.images.append(a)
        if tag=='details':self.details+=1
        if tag=='div':
            self.depth+=1
            if 'data-study-unit' in a:
                key=a['data-study-unit']
                if key in self.units:self.errors.append('duplicate study unit: '+key)
                self.active=key;self.level=self.depth;self.units[key]={'question':[],'answer':[]}
        if self.active and a.get('data-check') in ('question','answer'):
            self.role=a['data-check'];self.units[self.active][self.role].append('')
    def handle_data(self,data):
        if self.active and self.role:self.units[self.active][self.role][-1]+=data
    def handle_endtag(self,tag):
        if tag=='details':
            self.details-=1
            if self.details<0:self.errors.append('extra closing details')
        if tag in ('summary','p'):self.role=None
        if tag=='div':
            if self.active and self.depth==self.level:self.active=None
            self.depth-=1

def inspect(source,ledger,duration):
    p=Page();p.feed(source);errors=list(p.errors)
    if p.details:errors.append('unbalanced details')
    if len(p.ids)!=len(set(p.ids)):errors.append('duplicate id')
    for script in re.findall(r'<script[^>]*>(.*?)</script>',source,re.S):
        for target in re.findall(r"document\.querySelector\(\s*['\"]#([\w-]+)['\"]\s*\)",script):
            if target not in p.ids:errors.append('missing script target: '+target)
    if len(p.images)!=ledger['image_count']:errors.append('image count changed')
    if any(not i.get('src') or not i.get('alt') for i in p.images):errors.append('image without source or alt')
    for href in p.links:
        if href.startswith('#') and href[1:] not in p.ids:errors.append('broken anchor: '+href)
        u=urlparse(href)
        if u.hostname in ('www.youtube.com','youtube.com'):
            q=parse_qs(u.query)
            if q.get('v')==[ledger['video_id']] and q.get('t'):
                try:
                    if not 0<=int(q['t'][0].removesuffix('s'))<=duration:errors.append('timestamp out of bounds')
                except ValueError:errors.append('invalid timestamp')
    expected={u['id'] for u in ledger['units']}
    if set(p.units)!=expected:errors.append('study units and source ledger differ')
    for u in ledger['units']:
        if not 0<=u['source_start']<u['source_end']<=duration:errors.append('source range out of bounds: '+u['id'])
        for anchor in u.get('slides',[])+([u['topic']] if u.get('topic') else []):
            if anchor not in p.ids:errors.append('missing source target: '+anchor)
        for role in ('question','answer'):
            items=p.units.get(u['id'],{}).get(role,[])
            if not items or any(not x.strip() for x in items):errors.append('missing '+role+': '+u['id'])
        unit=p.units.get(u['id'],{})
        if len(unit.get('question',[]))!=len(unit.get('answer',[])):errors.append('question/answer count differs: '+u['id'])
    return errors

def main():
    root=Path(__file__).resolve().parents[1];fail=False
    manifests=sorted((root/'study-audits').glob('*.json'))
    if not manifests:
        print('FAIL: no study source records');return 1
    for path in manifests:
        ledger=json.loads(path.read_text(encoding='utf-8'));vid=ledger['video_id']
        source=(root/'lectures'/f'{vid}.html').read_text(encoding='utf-8')
        errors=inspect(source,ledger,ledger['duration_seconds'])
        print(vid+': '+('; '.join(errors) if errors else f"PASS ({len(ledger['units'])} teaching units, {ledger['image_count']} images)"))
        fail|=bool(errors)
    for file in [root/'concepts.html']+[root/'lectures'/f"{json.loads(p.read_text(encoding='utf-8'))['video_id']}.html" for p in manifests]:
        page=Page();page.feed(file.read_text(encoding='utf-8'))
        for href in page.links:
            url=urlparse(href)
            if url.scheme or url.netloc or not url.path.endswith('.html'):continue
            target=(file.parent/url.path).resolve()
            if not target.is_relative_to(root):
                print('FAIL: link outside repository '+href);fail=True;continue
            if not target.exists():
                print('FAIL: missing cross-page target '+href);fail=True;continue
            if url.fragment:
                other=Page();other.feed(target.read_text(encoding='utf-8'))
                if url.fragment not in other.ids:print('FAIL: missing cross-page anchor '+href);fail=True
    return int(fail)
if __name__=='__main__':sys.exit(main())
