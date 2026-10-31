# -*- coding: utf-8 -*-
"""Build the hub from the lecture registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
R=Path(__file__).resolve().parents[1]
def header(base='',active='lectures'):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html">내면을 공부하는 시간<small>강의 학습 아카이브</small></a><nav class="global-nav" aria-label="주요 메뉴"><a href="{base}index.html"'+(' aria-current="page"' if active=='lectures' else '')+f'>강의 모음</a><a href="{base}concepts.html"'+(' aria-current="page"' if active=='concepts' else '')+f'>용어와 개념</a><a href="{base}study-history.html"'+(' aria-current="page"' if active=='history' else '')+f'>학습 이력</a></nav></div></header>'
def footer(base=''):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>내면을 공부하는 시간 · 강의 학습</span><a href="{base}index.html">강의 모음으로</a><a href="{base}concepts.html">용어와 개념</a></div></footer>'
def page(title,body,base='',active='lectures'):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="강의가 중요한 이유와 배울 점을 먼저 읽고, 해설과 타임라인으로 학습하는 아카이브"><title>{html.escape(title)} · 내면을 공부하는 시간</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{base}assets/apple-touch-icon.png"><link rel="stylesheet" href="{base}assets/site.css?v=20261031-summary"><script defer src="{base}assets/site.js?v=20261031-chip"></script></head><body>{header(base,active)}{body}{footer(base)}</body></html>'
def render(rows):
    # 목록의 순서는 개인 학습용 편집 순서. 날짜가 없는 강의에는 임의의 공개일을 만들지 않는다.
    latest=rows[0]
    chips='<button data-filter-for="search" data-value="">전체</button>'
    for tag in dict.fromkeys(row.get('filter_tag', row['tags'][0]) for row in rows):
        label=html.escape(tag, quote=True)
        chips+=f'<button data-filter-for="search" data-value="{label}">{label}</button>'
    learning=['vHuZh8xLcDc','izYj8g-j00U','hw4_kLaHOMg','ZCty0wvogDo']
    reasons=['명상 전통과 훈련의 차이를 이해합니다.','긍정 기억을 구체적으로 떠올리며 정서 조절을 공부합니다.','용서와 책임 추궁을 구별합니다.','사실을 인정하면서도 행동할 수 있음을 이해합니다.']
    by_id={row['id']:row for row in rows}
    steps=''.join(f'<li><a href="lectures/{vid}.html">{html.escape(by_id[vid]["title"])}</a><p>{reason}</p></li>' for vid,reason in zip(learning,reasons) if vid in by_id)
    path=f'<section class="learning-route" aria-labelledby="learning-route-title"><h2 id="learning-route-title">연결해서 공부하기</h2><ol>{steps}</ol></section>' if steps else ''
    cards=''
    for i,row in enumerate(rows):
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in row['tags'])
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-search="{html.escape(" ".join(row["tags"]),quote=True)}" href="lectures/{row["id"]}.html"><div class="meta">'+('<span class="badge">최근 강의</span>' if i==0 else '')+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time>' if row.get("date") else '')+f'<span>{html.escape(row["duration"])}</span></div><h3>{html.escape(row["title"])}</h3><p>{html.escape(row["description"])}</p><div class="tags">{tags}</div><span class="read">해설로 공부하기 →</span></a>'
    body=f'''<div class="site-shell"><section id="settings" class="settings-panel" aria-label="계정 설정" hidden><h2>계정</h2><p id="account-state" role="status" aria-live="polite">로그인 상태를 확인하는 중입니다.</p><div class="actions"><button type="button" class="btn" id="account-action" disabled>구글로 로그인</button><a class="btn secondary" id="account-history" href="study-history.html" hidden>학습 이력 보기</a></div></section><div class="hub-hero"><div class="page-hero"><span class="eyebrow">개인 학습 아카이브</span><h1>나의 강의 학습 노트</h1><div class="actions"><a class="btn" href="#lectures">강의 고르기</a><button type="button" class="btn secondary" id="settings-toggle" aria-controls="settings" aria-expanded="false">설정</button><a class="btn secondary" href="concepts.html">용어부터 찾아보기</a></div></div><aside class="panel latest-entry" aria-label="최근 강의"><span class="eyebrow">{"최근 강의 · "+latest["date"].replace("-",".") if latest.get("date") else "최근 추가한 강의"}</span><h2>{html.escape(latest["title"])}</h2><p>{html.escape(latest["description"])}</p><a href="lectures/{latest["id"]}.html#overview">핵심 요약부터 읽기 →</a></aside></div><main id="main"><section id="lectures"><div class="section-heading"><h2>강의 모음</h2><span class="meta">학습 목록</span></div><div class="search-panel"><label for="search">주제로 찾기</label><input class="search" id="search" type="search" placeholder="기억, 편도체, 마음챙김…" data-filter-input="#lecture-list" data-count="count" data-empty="empty" data-noun="강의"><div class="filter-chips">{chips}</div><p class="search-summary" id="count" aria-live="polite">{len(rows)}개 강의</p></div><div class="lecture-grid" id="lecture-list">{cards}</div><p class="empty" id="empty" hidden>찾는 강의가 없습니다. 다른 단어로 검색하거나 ‘전체’를 선택합니다.</p></section>{path}</main></div>'''
    body+='<script type="module" src="assets/account.js?v=20261031-copy"></script>'
    return page('강의 모음',body)

def build(check=False):
    result=render(json.loads((R/'lectures.json').read_text(encoding='utf-8')))
    target=R/'index.html'
    if check:
        matches=target.read_text(encoding='utf-8')==result
        print('PASS: generated home matches index.html' if matches else 'FAIL: regenerate index.html with scripts/build_library.py')
        return 0 if matches else 1
    target.write_text(result,encoding='utf-8')
    return 0

if __name__=='__main__':sys.exit(build('--check' in sys.argv))
