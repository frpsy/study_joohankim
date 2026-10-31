# -*- coding: utf-8 -*-
"""강의별 5분 요약 페이지 생성: python scripts/build_summaries.py [--check]"""
from pathlib import Path
import html,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_library import page,R
READ_MINUTES='약 5분'
def esc(x):return html.escape(x,quote=False)
def render(row,data):
    vid=row['id'];lec=f'../lectures/{vid}.html';t=esc(row['title'])
    secs=''.join(f'<h2>{esc(s["h"])}</h2>'+''.join(f'<p>{esc(p)}</p>' for p in s['p']) for s in data['sections'])
    todo=''.join(f'<li>{esc(x)}</li>' for x in data['takeaways'])
    body=(f'<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">강의 모음</a><span aria-hidden="true">/</span><a href="{lec}">{t}</a><span aria-hidden="true">/</span><span>5분 요약</span></nav>'
      f'<main id="main"><article class="summary-page"><header class="summary-head"><span class="eyebrow">5분 요약</span><h1>{t}</h1><p class="meta">{esc(row["date"])} · 원본 {esc(row["duration"])} · 읽는 시간 {READ_MINUTES}</p></header>'
      f'<p class="summary-lead">{esc(data["lead"])}</p>{secs}'
      f'<h2>적용</h2><ul class="summary-list">{todo}</ul>'
      f'<aside class="summary-note" aria-label="읽을 때 유의할 점"><h2>유의할 점</h2><p>{esc(data["note"])}</p></aside>'
      f'<nav class="summary-links" aria-label="관련 페이지"><a class="btn" href="{lec}">주제별 해설</a><a class="btn secondary" href="{lec}#lecture-comment">타임라인</a><a class="btn secondary" href="../index.html">강의 모음</a></nav>'
      f'</article></main></div>')
    return page(f'{row["title"]} 5분 요약',body,base='../')
def build(check=False):
    rows={r['id']:r for r in json.loads((R/'lectures.json').read_text(encoding='utf-8'))}
    data=json.loads((R/'data/summaries.json').read_text(encoding='utf-8'));issues=[]
    for vid in rows:
        if vid not in data:issues.append('요약 누락: '+vid)
    for vid in data:
        if vid not in rows:issues.append('등록되지 않은 강의 요약: '+vid)
    for vid in sorted(set(rows)&set(data)):
        out=render(rows[vid],data[vid]);p=R/'summaries'/f'{vid}.html'
        if check:
            if not p.is_file() or p.read_bytes().decode('utf-8')!=out:issues.append(f'summaries/{vid}.html 이 data/summaries.json 과 다릅니다')
        else:
            p.parent.mkdir(exist_ok=True);p.write_bytes(out.encode('utf-8'))
    if check:print('\n'.join(issues) if issues else 'PASS: 5분 요약이 원고와 일치합니다')
    return bool(issues)
if __name__=='__main__':sys.exit(build('--check' in sys.argv))
