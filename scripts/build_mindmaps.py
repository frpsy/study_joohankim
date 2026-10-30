# -*- coding: utf-8 -*-
"""Build each lecture's semantic, responsive concept map from its reviewed outline."""
from pathlib import Path
from html import escape
import json,re,sys
R=Path(__file__).resolve().parents[1]
START='<!-- lecture-mindmap:start -->'
END='<!-- lecture-mindmap:end -->'
def render(outline):
    branches=''
    for title,leaves in outline['branches']:
        links=''.join(f'<li><a href="#{escape(anchor,quote=True)}">{escape(label)}</a></li>' for label,anchor in leaves)
        branches+=f'<li class="mindmap-branch"><h3>{escape(title)}</h3><ul>{links}</ul></li>'
    return START+'<section id="lecture-mindmap" class="lecture-section"><h2>마인드맵</h2>'+f'<div class="mindmap" role="group" aria-label="강의 핵심 개념 연결"><p class="mindmap-root">{escape(outline["root"])}</p><ul class="mindmap-branches">{branches}</ul></div></section>'+END

def errors(root):
    outlines=json.loads((root/'data/lecture_mindmaps.json').read_text(encoding='utf-8'))
    registry=json.loads((root/'lectures.json').read_text(encoding='utf-8'))
    result=[]
    for row in registry:
        vid=row['id'];page=root/'lectures'/f'{vid}.html'
        if vid not in outlines:result.append('mindmap outline missing: '+vid);continue
        if not page.is_file():continue
        source=page.read_text(encoding='utf-8')
        if source.count(render(outlines[vid]))!=1:result.append('generated mindmap differs: '+vid)
    return result

def build(check=False):
    if check:
        issues=errors(R);print('\n'.join(issues) if issues else 'PASS: all lecture mindmaps match source outlines');return bool(issues)
    outlines=json.loads((R/'data/lecture_mindmaps.json').read_text(encoding='utf-8'))
    for vid,outline in outlines.items():
        p=R/'lectures'/f'{vid}.html'
        with p.open(encoding='utf-8',newline='') as f:source=f.read()
        rendered=render(outline)
        if START in source:
            pattern=re.compile(re.escape(START)+'.*?'+re.escape(END),re.S)
            assert len(pattern.findall(source))==1
            source=pattern.sub(lambda _:rendered,source,count=1)
        else:
            marker='<section id="lecture-details"'
            assert source.count(marker)==1
            source=source.replace(marker,rendered+marker,1)
            # Add the common map stage and renumber only the existing sidebar links.
            m=re.search(r'<aside class="sidebar".*?</aside>',source,re.S);assert m
            nav=m.group();links=re.findall(r'<a href="[^"]+">.*?</a>',nav,re.S)
            assert len(links)>=6
            rebuilt=[links[0],'<a href="#lecture-mindmap">02 마인드맵</a>']
            rebuilt.extend(re.sub(r'>\d{2} ',f'>{i:02d} ',link,count=1) for i,link in enumerate(links[1:],3))
            nav=nav[:nav.index(links[0])]+''.join(rebuilt)+'</aside>'
            source=source[:m.start()]+nav+source[m.end():]
        with p.open('w',encoding='utf-8',newline='') as f:f.write(source)
    return False
if __name__=='__main__':sys.exit(build('--check' in sys.argv))
