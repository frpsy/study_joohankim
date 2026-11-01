# -*- coding: utf-8 -*-
"""Build the hub from the lecture registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
R=Path(__file__).resolve().parents[1]
def header(base='',active='lectures'):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html"><img class="brand-symbol" src="{base}assets/icon.svg" width="32" height="32" alt="" aria-hidden="true"><span class="brand-name">내면의 서재<small>강의 · 개념 · 복습</small></span></a><nav class="global-nav" aria-label="주요 메뉴"><a href="{base}index.html"'+(' aria-current="page"' if active=='lectures' else '')+f'>강의 모음</a><a href="{base}concepts.html"'+(' aria-current="page"' if active=='concepts' else '')+f'>용어와 개념</a><a href="{base}study-history.html"'+(' aria-current="page"' if active=='history' else '')+f'>학습 이력</a></nav></div></header>'
def footer(base=''):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>내면의 서재 · 강의 학습</span><a href="{base}index.html">강의 모음으로</a><a href="{base}concepts.html">용어와 개념</a></div></footer>'
def page(title,body,base='',active='lectures'):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="김주환 강의의 핵심을 읽고 개념을 연결하며 복습하는 개인 학습 서재"><title>내면의 서재 · {html.escape(title)}</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{base}assets/apple-touch-icon.png"><link rel="stylesheet" href="{base}assets/site.css?v=20261101-editorial-v7"><script defer src="{base}assets/site.js?v=20261101-editorial-v7"></script></head><body>{header(base,active)}{body}{footer(base)}</body></html>'
def render(rows):
    # 목록의 순서는 개인 학습용 편집 순서. 날짜가 없는 강의에는 임의의 공개일을 만들지 않는다.
    latest=rows[0]
    chips='<button data-filter-for="search" data-value="">전체</button>'
    for tag in dict.fromkeys(row.get('filter_tag', row['tags'][0]) for row in rows):
        label=html.escape(tag, quote=True)
        chips+=f'<button data-filter-for="search" data-value="{label}">{label}</button>'
    learning=['vHuZh8xLcDc','izYj8g-j00U','xA-4G4z-1MM','hw4_kLaHOMg','ZCty0wvogDo','QmOF0crdyRU']
    reasons=['명상 전통과 훈련 방식의 차이','긍정 기억의 구체성과 정서 조절','몸의 긴장과 두려움·집착의 관계','용서와 책임 추궁의 차이','사실 인정과 변화 행동의 양립','원함과 즐거움, 행동을 이끄는 동기']
    by_id={row['id']:row for row in rows}
    steps=''.join(f'<li><a href="mini-courses/{vid}.html">{html.escape(by_id[vid]["title"])}</a><p>{reason}</p></li>' for vid,reason in zip(learning,reasons) if vid in by_id)
    path=f'<section class="learning-route" aria-labelledby="learning-route-title"><h2 id="learning-route-title">미니강좌</h2><ol>{steps}</ol></section>' if steps else ''
    cards=''
    for i,row in enumerate(rows):
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in row['tags'])
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-search="{html.escape(" ".join(row["tags"]),quote=True)}" href="lectures/{row["id"]}.html"><div class="meta">'+('<span class="badge">최근 정리</span>' if i==0 else '')+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time>' if row.get("date") else '')+f'<span>{html.escape(row["duration"])}</span></div><h3>{html.escape(row["title"])}</h3><p>{html.escape(row["description"])}</p><div class="tags">{tags}</div><span class="read">3단 요약과 타임라인 →</span></a>'
    body=f'''<div class="site-shell"><div class="hub-hero mobile-hub"><div class="page-hero"><span class="eyebrow hero-eyebrow">개인 학습 아카이브</span><h1>강의에서 시작하는<br class="hero-title-break"> 내면 공부</h1><p class="hero-description">김주환 교수의 강의를 요약과 미니강좌, 핵심 개념으로 정리한 개인 학습 서재</p><div class="actions hub-actions"><a class="btn" href="#lectures">강의 고르기</a><a class="btn secondary" href="#learning-route-title">미니강좌</a><button type="button" class="btn secondary" id="settings-toggle" aria-controls="settings" aria-expanded="false">로그인 · 계정</button></div><section id="settings" class="settings-panel" aria-label="계정 설정" hidden><div class="account-header"><h2>내 계정</h2><button type="button" class="btn secondary account-close" id="account-close" aria-label="계정 패널 닫기">닫기</button></div><p id="account-state" role="status" aria-live="polite">로그인 연결 중</p><div class="actions account-actions"><button type="button" class="btn" id="account-action" disabled>로그인 준비 중</button><a class="btn secondary" id="account-history" href="study-history.html" hidden>학습 이력</a></div><p class="account-hint">로그인 창이 열리지 않으면 Safari 또는 Chrome에서 사이트 주소를 직접 열어 주세요.</p></section></div><aside class="panel latest-entry" aria-label="최근 강의"><span class="eyebrow">{"최근 정리한 강의 · "+latest["date"].replace("-",".") if latest.get("date") else "최근 정리한 강의"}</span><h2>{html.escape(latest["title"])}</h2><a href="lectures/{latest["id"]}.html#overview">핵심 요약부터 읽기 →</a></aside></div><main id="main"><section id="lectures"><div class="section-heading"><h2>강의 모음</h2><span class="meta">학습 목록</span></div><div class="search-panel"><label for="search">주제로 찾기</label><input class="search" id="search" type="search" placeholder="기억, 편도체, 마음챙김…" data-filter-input="#lecture-list" data-count="count" data-empty="empty" data-noun="강의"><div class="filter-chips">{chips}</div><p class="search-summary" id="count" aria-live="polite">{len(rows)}개 강의</p></div><div class="lecture-grid" id="lecture-list">{cards}</div><p class="empty" id="empty" hidden>검색 결과 없음 · 다른 단어 또는 ‘전체’ 선택</p></section>{path}</main></div>'''
    body+='<script type="module" src="assets/account.js?v=20261101-auth-fix"></script>'
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
