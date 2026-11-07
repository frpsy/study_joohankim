# -*- coding: utf-8 -*-
"""Build the lecture list from the registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
R=Path(__file__).resolve().parents[1]
SITE_NAME='내면의 서재'
SITE_DESCRIPTOR='강의 요약 · 타임스탬프'
SITE_DESCRIPTION='강의의 핵심 요약과 타임스탬프를 모은 개인 학습 서재'
ASSET_VERSION=json.loads((R/'build-info.json').read_text(encoding='utf-8'))['version']
def header(base='',active='lectures'):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html"><img class="brand-symbol" src="{base}assets/icon.svg" width="32" height="32" alt="" aria-hidden="true"><span class="brand-name">{SITE_NAME}<small>{SITE_DESCRIPTOR}</small></span></a></div></header>'
def footer(base='',account=False):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>{SITE_NAME}</span><a href="{base}index.html">강의 목록</a><button type="button" class="theme-toggle" data-theme-toggle aria-label="화면 테마 변경">화면 · 시스템</button></div></footer>'
def page(title,body,base='',active='lectures',account=False):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#ffffff"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="{SITE_NAME}"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="description" content="{SITE_DESCRIPTION}"><title>{SITE_NAME} · {html.escape(title)}</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" sizes="180x180" href="{base}assets/apple-touch-icon.png"><link rel="manifest" href="{base}manifest.webmanifest"><script src="{base}assets/theme.js?v={ASSET_VERSION}"></script><link rel="stylesheet" href="{base}assets/site.css?v={ASSET_VERSION}"><script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script></head><body>{header(base,active)}{body}{footer(base,account)}</body></html>'
def render(rows, materials=None):
    materials=materials or []
    # 목록 순서는 레지스트리 배열 순서이다. 날짜가 없는 강의에는 임의의 공개일을 만들지 않는다.
    chips='<button data-filter-for="search" data-value="">전체</button>'
    for tag in dict.fromkeys(row.get('filter_tag', row['tags'][0]) for row in rows+materials):
        label=html.escape(tag, quote=True)
        chips+=f'<button data-filter-for="search" data-value="{label}">{label}</button>'
    cards=''
    for row in rows:
        creator=html.escape(row.get('creator','출처 미기재'))
        searchable=html.escape(" ".join([row['title'],row.get('description',''),row.get('creator','')]+row['tags']),quote=True)
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in row['tags'])
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-kind="lecture" data-creator="{html.escape(row.get("creator",""),quote=True)}" data-search="{searchable}" href="lectures/{row["id"]}.html"><div class="meta">'+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time>' if row.get("date") else '')+f'<span>{html.escape(row["duration"])}</span><span class="creator">{creator}</span></div><h2>{html.escape(row["title"])}</h2><p>{html.escape(row["description"])}</p><div class="tags">{tags}</div><span class="read">'+("핵심 요약과 타임스탬프 →" if row.get("creator","김주환")=="김주환" else "상세 요약 →")+'</span></a>'
    # Other material types have their own pages and are not assumed to have a YouTube ID.
    type_names={'book':'책','paper':'연구','article':'글','note':'학습 노트'}
    for item in materials:
        kind=item['kind']
        if kind not in type_names:raise ValueError('지원하지 않는 자료 유형: '+kind)
        url=item['url']
        if not isinstance(url,str) or not url or url.startswith(('/', '#')) or ':' in url or '..' in url.split('/'):
            raise ValueError('자료 주소는 사이트 내부 상대 경로만 허용합니다')
        creator=html.escape(item.get('creator','출처 미기재'))
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in item['tags'])
        searchable=html.escape(" ".join([item['title'],item.get('description',''),item.get('creator',''),kind]+item['tags']),quote=True)
        cards+=f'<a class="lecture" data-kind="{kind}" data-search="{searchable}" href="{html.escape(url,quote=True)}"><div class="meta"><span>{type_names[kind]}</span><span class="creator">{creator}</span></div><h2>{html.escape(item["title"])}</h2><p>{html.escape(item.get("description",""))}</p><div class="tags">{tags}</div><span class="read">자료 읽기 →</span></a>'
    total=len(rows)+len(materials)
    noun='자료' if materials else '강의'
    body=f'''<div class="site-shell"><main id="main" class="home-main"><section id="lectures"><div id="home-catalog"><h1 class="home-title">강의 요약</h1><div class="search-panel"><label for="search">{noun} 검색</label><div class="search-controls"><input class="search" id="search" type="search" placeholder="제목, 강연자, 주제로 검색" data-filter-input="#home-catalog" data-count="count" data-empty="empty" data-noun="{noun}" data-persist-query="true"><button type="button" class="btn secondary" data-clear-for="search" hidden>초기화</button></div><div class="filter-chips">{chips}</div><p class="search-summary" id="count" aria-live="polite">{total}개 {noun}</p></div><div class="lecture-grid" id="lecture-list">{cards}</div></div><p class="empty" id="empty" hidden>검색 결과가 없습니다. 다른 단어로 찾거나 ‘전체’를 선택해 주세요.</p></section></main></div>'''
    return page('강의 요약',body)

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
