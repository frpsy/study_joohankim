# -*- coding: utf-8 -*-
"""Build the hub from the lecture registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
R=Path(__file__).resolve().parents[1]
SITE_NAME='내면의 서재'
SITE_DESCRIPTOR='강의 · 개념 · 미니강좌'
ASSET_VERSION=json.loads((R/'build-info.json').read_text(encoding='utf-8'))['version']
def header(base='',active='lectures'):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html"><img class="brand-symbol" src="{base}assets/icon.svg" width="32" height="32" alt="" aria-hidden="true"><span class="brand-name">{SITE_NAME}<small>{SITE_DESCRIPTOR}</small></span></a><nav class="global-nav" aria-label="주요 메뉴"><a href="{base}index.html"'+(' aria-current="page"' if active=='lectures' else '')+f'>자료 모음</a><a href="{base}concepts.html"'+(' aria-current="page"' if active=='concepts' else '')+f'>용어와 개념</a></nav></div></header>'
def footer(base='',account=False):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>{SITE_NAME}</span><a href="{base}index.html">자료 모음으로</a><a href="{base}concepts.html">용어와 개념</a><button type="button" class="theme-toggle" data-theme-toggle aria-label="화면 테마 변경">화면 · 시스템</button></div></footer>'
def page(title,body,base='',active='lectures',account=False):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#f6f4ee"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="내면의 서재"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="description" content="강의, 책, 연구와 사유를 연결하며 배우고 정리하는 개인 학습 서재"><title>{SITE_NAME} · {html.escape(title)}</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" sizes="180x180" href="{base}assets/apple-touch-icon.png"><link rel="manifest" href="{base}manifest.webmanifest"><script src="{base}assets/theme.js?v={ASSET_VERSION}"></script><link rel="stylesheet" href="{base}assets/site.css?v={ASSET_VERSION}"><script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script></head><body>{header(base,active)}{body}{footer(base,account)}</body></html>'
def render(rows, materials=None):
    materials=materials or []
    # 목록의 순서는 개인 학습용 편집 순서. 날짜가 없는 강의에는 임의의 공개일을 만들지 않는다.
    latest=rows[0] if rows else None
    selected=[item for item in materials if item.get('featured')]
    if len(selected)>1:raise ValueError('대표 자료는 하나만 선택할 수 있습니다')
    featured_material=selected[0] if selected else None
    chips='<button data-filter-for="search" data-value="">전체</button>'
    for tag in dict.fromkeys(row.get('filter_tag', row['tags'][0]) for row in rows+materials):
        label=html.escape(tag, quote=True)
        chips+=f'<button data-filter-for="search" data-value="{label}">{label}</button>'
    learning=['vHuZh8xLcDc','izYj8g-j00U','xA-4G4z-1MM','hw4_kLaHOMg','ZCty0wvogDo','QmOF0crdyRU']
    reasons=['명상 전통과 훈련 방식의 차이','긍정 기억의 구체성과 정서 조절','몸의 긴장과 두려움·집착의 관계','용서와 책임 추궁의 차이','사실 인정과 변화 행동의 양립','원함과 즐거움, 행동을 이끄는 동기']
    by_id={row['id']:row for row in rows}
    steps=''.join(f'<li><a href="mini-courses/{vid}.html">{html.escape(by_id[vid]["title"])}</a><p>{reason}</p></li>' for vid,reason in zip(learning,reasons) if vid in by_id)
    path=f'<section class="learning-route" aria-labelledby="learning-route-title"><h2 id="learning-route-title">미니강좌</h2><ol>{steps}</ol></section>' if steps else ''
    cards=''
    for i,row in enumerate(rows):
        if i==0 and featured_material is None:continue
        creator=html.escape(row.get('creator','출처 미기재'))
        searchable=html.escape(" ".join([row['title'],row.get('description',''),row.get('creator','')]+row['tags']),quote=True)
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in row['tags'])
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-kind="lecture" data-creator="{html.escape(row.get("creator",""),quote=True)}" data-search="{searchable}" href="lectures/{row["id"]}.html"><div class="meta">'+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time>' if row.get("date") else '')+f'<span>{html.escape(row["duration"])}</span><span class="creator">{creator}</span></div><h3>{html.escape(row["title"])}</h3><p>{html.escape(row["description"])}</p><div class="tags">{tags}</div><span class="read">핵심 요약과 타임라인 →</span></a>'
    # Other material types have their own pages and are not assumed to have a YouTube ID.
    # Keep existing lecture URLs and stable content IDs intact.
    type_names={'book':'책','paper':'연구','article':'글','note':'학습 노트'}
    for item in materials:
        kind=item['kind']
        if kind not in type_names:raise ValueError('지원하지 않는 자료 유형: '+kind)
        url=item['url']
        if not isinstance(url,str) or not url or url.startswith(('/', '#')) or ':' in url or '..' in url.split('/'):
            raise ValueError('자료 주소는 사이트 내부 상대 경로만 허용합니다')
        if item is featured_material:continue
        creator=html.escape(item.get('creator','출처 미기재'))
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in item['tags'])
        searchable=html.escape(" ".join([item['title'],item.get('description',''),item.get('creator',''),kind]+item['tags']),quote=True)
        cards+=f'<a class="lecture" data-kind="{kind}" data-search="{searchable}" href="{html.escape(url,quote=True)}"><div class="meta"><span>{type_names[kind]}</span><span class="creator">{creator}</span></div><h3>{html.escape(item["title"])}</h3><p>{html.escape(item.get("description",""))}</p><div class="tags">{tags}</div><span class="read">자료 읽기 →</span></a>'
    total=len(rows)+len(materials)
    featured=''
    if featured_material is not None:
        item=featured_material
        kind=item['kind']
        url=item['url']
        type_label=type_names[kind]
        searchable=html.escape(" ".join([item['title'],item.get('description',''),item.get('creator',''),kind]+item['tags']),quote=True)
        featured=f'<a class="home-feature" data-kind="{kind}" data-creator="{html.escape(item.get("creator",""),quote=True)}" data-search="{searchable}" href="{html.escape(url,quote=True)}"><span class="eyebrow">대표 {type_label}</span><h2>{html.escape(item["title"])}</h2><p>{html.escape(item.get("description",""))}</p><span class="home-feature-action">자료 본문 읽기 →</span></a>'
    elif latest:
        searchable=html.escape(" ".join([latest['title'],latest.get('description',''),latest.get('creator','')]+latest['tags']),quote=True)
        featured=f'<a class="home-feature" data-kind="lecture" data-video-id="{latest["id"]}" data-creator="{html.escape(latest.get("creator",""),quote=True)}" data-search="{searchable}" href="lectures/{latest["id"]}.html"><span class="eyebrow">대표 강의</span><h2>{html.escape(latest["title"])}</h2><p>{html.escape(latest["description"])}</p><span class="home-feature-action">강의 본문 읽기 →</span></a>'
    course_link='<a class="home-course-link" href="#learning-route-title">미니강좌 보기 →</a>' if steps else ''
    body=f'''<div class="site-shell"><main id="main" class="home-main"><section id="lectures"><div id="home-catalog"><div class="home-overview"><div class="home-overview-heading"><h1>학습 자료</h1>{course_link}</div>{featured}</div><div class="search-panel"><label for="search">자료 검색</label><div class="search-controls"><input class="search" id="search" type="search" placeholder="주제, 이름, 키워드 검색…" data-filter-input="#home-catalog" data-count="count" data-empty="empty" data-noun="자료" data-persist-query="true"><button type="button" class="btn secondary" data-clear-for="search" hidden>초기화</button></div><div class="filter-chips">{chips}</div><p class="search-summary" id="count" aria-live="polite">{total}개 자료</p></div><div class="lecture-grid" id="lecture-list">{cards}</div></div><p class="empty" id="empty" hidden>검색 결과 없음 · 다른 단어 또는 ‘전체’ 선택</p></section>{path}</main></div>'''
    return page('자료 모음',body)

def build(check=False):
    result=render(json.loads((R/'lectures.json').read_text(encoding='utf-8')),json.loads((R/'materials.json').read_text(encoding='utf-8')))
    target=R/'index.html'
    if check:
        matches=target.read_text(encoding='utf-8')==result
        print('PASS: generated home matches index.html' if matches else 'FAIL: regenerate index.html with scripts/build_library.py')
        if not matches:
            current=target.read_text(encoding='utf-8')
            first=next((i for i,(a,b) in enumerate(zip(result,current)) if a!=b),min(len(result),len(current)))
            print('First mismatch at',first)
            print('Expected:',repr(result[max(0,first-100):first+180]))
            print('Actual:  ',repr(current[max(0,first-100):first+180]))
        return 0 if matches else 1
    target.write_text(result,encoding='utf-8')
    return 0

if __name__=='__main__':sys.exit(build('--check' in sys.argv))
