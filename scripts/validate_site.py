"""Check common layout, registry and local link graph. Run python scripts/validate_site.py."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import json,sys
class Document(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.hrefs=[];self.styles=[];self.scripts=[];self.h1=0;self.header=0;self.notes=False;self.inline_style=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        if tag=='a':self.hrefs.append(a.get('href',''))
        if tag=='link' and a.get('rel')=='stylesheet':self.styles.append(a.get('href',''))
        if tag=='script' and a.get('src'):self.scripts.append(a['src'])
        if tag=='h1':self.h1+=1
        if tag=='header' and a.get('class')=='site-header':self.header+=1
        if a.get('id') in ('notes','note','download-note'):self.notes=True
        if tag=='style' or 'style' in a:self.inline_style=True
def structural_errors(text):
    d=Document();d.feed(text);errors=[]
    if d.header!=1:errors.append('common header missing or duplicated')
    if d.h1!=1:errors.append('expected one page title')
    if 'main' not in d.ids:errors.append('skip target missing')
    if len(d.ids)!=len(set(d.ids)):errors.append('duplicate id')
    if not any(x.endswith('assets/site.css') for x in d.styles):errors.append('shared stylesheet missing')
    if not any(x.endswith('assets/site.js') for x in d.scripts):errors.append('shared behavior missing')
    if d.notes:errors.append('removed note UI reintroduced')
    if d.inline_style:errors.append('page-specific inline style reintroduced')
    return errors,d
def validate(root):
    rows=json.loads((root/'lectures.json').read_text(encoding='utf-8'));errors=[];docs={}
    if len({x['id'] for x in rows})!=len(rows):errors.append('duplicate video in registry')
    pages=[root/'index.html',root/'concepts.html']+[root/'lectures'/f"{r['id']}.html" for r in rows]
    for p in pages:
        if not p.is_file():errors.append('missing page '+str(p));continue
        problems,d=structural_errors(p.read_text(encoding='utf-8'));docs[p.resolve()]=d
        errors.extend(p.name+': '+x for x in problems)
    for p,d in docs.items():
        for href in d.hrefs+d.styles+d.scripts:
            u=urlparse(href)
            if u.scheme or u.netloc:continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            if not target.is_relative_to(root.resolve()):errors.append('link outside root: '+href);continue
            if not target.is_file():errors.append(p.name+': missing target '+href);continue
            if u.fragment and target in docs and unquote(u.fragment) not in docs[target].ids:errors.append(p.name+': missing anchor '+href)
    home=(root/'index.html').read_text(encoding='utf-8')
    for row in rows:
        if home.count('data-video-id="'+row['id']+'"')!=1:errors.append('hub card mismatch '+row['id'])
    return errors
if __name__=='__main__':
    result=validate(Path(__file__).resolve().parents[1])
    print('\n'.join(result) if result else 'PASS: common design, lecture registry and complete local link graph')
    sys.exit(bool(result))
