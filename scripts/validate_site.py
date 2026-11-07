"""Check common layout, registry and local link graph. Run python scripts/validate_site.py."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import re,json,sys
from build_library import render
from content_registry import validate_catalog
from build_mindmaps import errors as mindmap_errors
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
    if not any(urlparse(x).path.endswith('assets/site.css') for x in d.styles):errors.append('shared stylesheet missing')
    if not any(urlparse(x).path.endswith('assets/site.js') for x in d.scripts):errors.append('shared behavior missing')
    if d.notes:errors.append('removed note UI reintroduced')
    if d.inline_style:errors.append('page-specific inline style reintroduced')
    return errors,d
def lecture_layout_errors(source):
    d=Document();d.feed(source);errors=[]
    compact='data-layout="compact"' in source
    timed='id="lecture-comment"' in source
    required=['lecture-overview','lecture-comment' if timed else 'lecture-detail'] if compact else ['lecture-overview','lecture-mindmap','lecture-details','lecture-practice','lecture-sources','lecture-comment']
    if any(id not in d.ids for id in required):errors.append('standard lecture section missing')
    else:
        positions=[d.ids.index(id) for id in required]
        if positions!=sorted(positions):errors.append('standard lecture section order differs')
    import re
    if (not compact or timed) and 'data-copy-target=' not in source:errors.append('shared comment copy missing')
    if (not compact or timed) and not re.search(r'<span[^>]*id="status"[^>]*role="status"[^>]*aria-live="polite"',source):errors.append('accessible copy status missing')
    if not compact and 'data-expand-scope="#lecture-details"' not in source:errors.append('shared expand controls missing')
    return errors

def validate(root):
    rows=json.loads((root/'lectures.json').read_text(encoding='utf-8'));errors=validate_catalog(root);docs={}
    if len({x['id'] for x in rows})!=len(rows):errors.append('duplicate video in registry')
    materials=json.loads((root/'materials.json').read_text(encoding='utf-8')) if (root/'materials.json').exists() else []
    if not isinstance(materials,list):errors.append('materials registry must be a list');materials=[]
    valid_types={'book','paper','article','note'}
    material_ids=set()
    for item in materials:
        if not isinstance(item,dict) or not {'id','kind','title','creator','url','tags'}.issubset(item):errors.append('invalid material record');continue
        if item['id'] in material_ids or item['id'] in {row['id'] for row in rows}:errors.append('duplicate material id '+str(item['id']))
        material_ids.add(item['id'])
        if item['kind'] not in valid_types:errors.append('invalid material kind '+str(item['kind']))
        if not isinstance(item['tags'],list):errors.append('invalid material tags '+str(item['id']))
    pages=[root/'index.html']+[root/'lectures'/f"{r['id']}.html" for r in rows]
    for p in pages:
        if not p.is_file():errors.append('missing page '+str(p));continue
        source=p.read_text(encoding='utf-8')
        problems,d=structural_errors(source);docs[p.resolve()]=d
        if p.parent.name=='lectures':
            problems.extend(lecture_layout_errors(source))
            if 'id="why"' in source or '이 강의에서 얻을 수 있는 것' in source:problems.append('separate goals block reintroduced; merge it into the hero intro')
            m=re.search(r'</h1><p[^>]*>(.*?)</p>',source)
            if 'data-layout="compact"' not in source and (not m or len(m.group(1))<150):problems.append('hero intro must state why it matters and what the lecture gives')
        if p.parent.name=='lectures':
            kim=next((r.get('creator')=='김주환' for r in rows if r['id']==p.stem),True)
            if kim!=('id="lecture-comment"' in source):problems.append('timestamps belong only to 김주환 lectures; others need a detailed summary')
        errors.extend(p.name+': '+x for x in problems)
    for p,d in docs.items():
        for href in d.hrefs+d.styles+d.scripts:
            u=urlparse(href)
            if u.scheme or u.netloc:continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            if not target.is_relative_to(root.resolve()):errors.append('link outside root: '+href);continue
            if not target.is_file():errors.append(p.name+': missing target '+href);continue
            if u.fragment and target in docs and unquote(u.fragment) not in docs[target].ids:errors.append(p.name+': missing anchor '+href)
    if (root/'data/lecture_mindmaps.json').is_file():errors.extend(mindmap_errors(root))
    home=(root/'index.html').read_text(encoding='utf-8')
    try:
        generated=render(rows,materials)
        if home!=generated:
            errors.append('generated home differs from index.html')
            first=next((i for i,(a,b) in enumerate(zip(generated,home)) if a!=b),min(len(generated),len(home)))
            errors.append('first difference '+str(first)+' generated '+repr(generated[max(0,first-80):first+130])+' saved '+repr(home[max(0,first-80):first+130]))
    except (ValueError,KeyError,TypeError) as exc:errors.append('invalid material registry: '+str(exc))
    for row in rows:
        if home.count('data-video-id="'+row['id']+'"')!=1:errors.append('hub card mismatch '+row['id'])
    return errors
if __name__=='__main__':
    result=validate(Path(__file__).resolve().parents[1])
    print('\n'.join(result) if result else 'PASS: common design, lecture registry and complete local link graph')
    sys.exit(bool(result))
