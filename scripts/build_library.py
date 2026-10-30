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
    rows=json.loads((R/'lectures.json').read_text(encoding='utf-8'))
    # 목록의 순서는 개인 학습용 편집 순서. 날짜가 없는 강의에는 임의의 공개일을 만들지 않는다.
    latest=rows[0]
    cards=''
    for i,row in enumerate(rows):
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in row['tags'])
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-search="{html.escape(" ".join(row["tags"]),quote=True)}" href="lectures/{row["id"]}.html"><div class="meta">'+('<span class="badge">최근 강의</span>' if i==0 else '')+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time>' if row.get("date") else '')+f'<span>{row["duration"]}</span></div><h3>{row["title"]}</h3><p>{row["description"]}</p><div class="tags">{tags}</div><span class="read">해설로 공부하기 →</span></a>'
    body=f'''<div class="site-shell"><div class="hub-hero"><div class="page-hero"><span class="eyebrow">개인 학습 아카이브</span><h1>나의 강의 학습 노트</h1><p class="lead">개념을 이해하고 질문으로 복습하며,<br>원본 영상의 필요한 구간을 다시 찾아봅니다.</p><div class="actions"><a class="btn" href="#lectures">강의 고르기</a><a class="btn secondary" href="concepts.html">용어부터 찾아보기</a></div></div><aside class="panel latest-entry" aria-label="최근 강의"><span class="eyebrow">최근 강의 · {latest["date"].replace("-",".") if latest.get("date") else "최근 추가"}</span><h2>{latest["title"]}</h2><p>{latest["description"]}</p><a href="lectures/{latest["id"]}.html#overview">핵심 요약부터 읽기 →</a></aside></div><main id="main"><section id="lectures"><div class="section-heading"><h2>강의 모음</h2><span class="meta">학습 목록</span></div><div class="search-panel"><label for="search">주제로 찾기</label><input class="search" id="search" type="search" placeholder="기억, 편도체, 마음챙김…" data-filter-input="#lecture-list" data-count="count" data-empty="empty" data-noun="강의"><div class="filter-chips"><button data-filter-for="search" data-value="">전체</button><button data-filter-for="search" data-value="긍정 기억">긍정 기억</button><button data-filter-for="search" data-value="명상">명상</button><button data-filter-for="search" data-value="수용">수용</button><button data-filter-for="search" data-value="도파민">도파민</button></div><p class="search-summary" id="count" aria-live="polite">{len(rows)}개 강의</p></div><div class="lecture-grid" id="lecture-list">{cards}</div><p class="empty" id="empty" hidden>찾는 강의가 없습니다. 다른 단어나 ‘전체’를 선택해 보세요.</p></section></main></div>'''
    (R/'index.html').write_text(page('강의 모음',body),encoding='utf-8')
if __name__=='__main__':build()
