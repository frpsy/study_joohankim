"""Build the hub from the lecture registry: python scripts/build_library.py"""
from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1]
def header(base='',active='lectures'):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html">내면을 공부하는 시간<small>강의 학습 아카이브</small></a><nav class="global-nav" aria-label="주요 메뉴"><a href="{base}index.html"'+(' aria-current="page"' if active=='lectures' else '')+f'>강의 모음</a><a href="{base}concepts.html"'+(' aria-current="page"' if active=='concepts' else '')+'>용어와 개념</a></nav></div></header>'
def footer(base=''):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>내면을 공부하는 시간 · 강의 학습</span><a href="{base}index.html">강의 모음으로</a><a href="{base}concepts.html">용어와 개념</a></div></footer>'
def page(title,body,base='',active='lectures'):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="강의가 중요한 이유와 배울 점을 먼저 읽고, 해설과 타임라인으로 학습하는 아카이브"><title>{html.escape(title)} · 내면을 공부하는 시간</title><link rel="stylesheet" href="{base}assets/site.css"><script defer src="{base}assets/site.js"></script></head><body>{header(base,active)}{body}{footer(base)}</body></html>'
def build():
    rows=sorted(json.loads((R/'lectures.json').read_text(encoding='utf-8')),key=lambda x:x['date'],reverse=True)
    latest=rows[0]
    cards=''
    for i,row in enumerate(rows):
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in row['tags'])
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-search="{html.escape(" ".join(row["tags"]),quote=True)}" href="lectures/{row["id"]}.html"><div class="meta">'+('<span class="badge">최근 강의</span>' if i==0 else '')+f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time><span>{row["duration"]}</span></div><h3>{row["title"]}</h3><p>{row["description"]}</p><div class="tags">{tags}</div><span class="read">해설로 공부하기 →</span></a>'
    body=f'''<div class="site-shell"><div class="hub-hero"><div class="page-hero"><span class="eyebrow">강의를 읽고 이해하는 공간</span><h1>한 강의씩 쌓아가는<br>내면소통 공부</h1><p class="lead">강의가 중요한 이유와 배울 점부터 확인하고,<br>해설·질문·영상 타임라인으로 깊게 공부합니다.</p><div class="actions"><a class="btn" href="#lectures">강의 고르기</a><a class="btn secondary" href="concepts.html">용어부터 찾아보기</a></div></div><aside class="panel latest-entry" aria-label="최근 강의"><span class="eyebrow">최근 정리한 강의 · {latest["date"].replace("-",".")}</span><h2>{latest["title"]}</h2><p>{latest["description"]}</p><a href="lectures/{latest["id"]}.html#overview">핵심 요약부터 읽기 →</a></aside></div><main id="main"><section id="lectures"><div class="section-heading"><h2>강의 모음</h2><span class="meta">공개일 최신순</span></div><div class="search-panel"><label for="search">배우고 싶은 주제로 찾기</label><input class="search" id="search" type="search" placeholder="기억, 편도체, 마음챙김…" data-filter-input="#lecture-list" data-count="count" data-empty="empty" data-noun="강의"><div class="filter-chips"><button data-filter-for="search" data-value="">전체</button><button data-filter-for="search" data-value="긍정 기억">긍정 기억</button><button data-filter-for="search" data-value="명상">명상 전통</button></div><p class="search-summary" id="count" aria-live="polite">{len(rows)}개 강의</p></div><div class="lecture-grid" id="lecture-list">{cards}</div><p class="empty" id="empty" hidden>찾는 강의가 없습니다. 다른 단어나 ‘전체’를 선택해 보세요.</p></section><section id="guide" class="panel"><h2>처음 오셨다면</h2><p>강의의 핵심 요약을 읽은 뒤, 주제별 해설에서 개념과 이유를 이해하세요. 관련 화면을 대조하고 복습 질문에 답해 보면 영상 없이 읽을 때도, 시청 후 복습할 때도 흐름을 잡을 수 있습니다.</p><a href="concepts.html">헷갈리는 용어는 개념집에서 확인하기 →</a></section></main></div>'''
    (R/'index.html').write_text(page('강의 모음',body),encoding='utf-8')
if __name__=='__main__':build()
