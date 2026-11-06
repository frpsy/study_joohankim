# -*- coding: utf-8 -*-
"""Build the hub from the lecture registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
R=Path(__file__).resolve().parents[1]
SITE_NAME='김주환 강의 스터디'
ASSET_VERSION=json.loads((R/'build-info.json').read_text(encoding='utf-8'))['version']
def header(base='',active=None):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html"><img class="brand-symbol" src="{base}assets/icon.svg" width="32" height="32" alt="" aria-hidden="true"><span class="brand-name">{SITE_NAME}</span></a><nav class="global-nav" aria-label="주요 메뉴"><a href="{base}index.html"'+(' aria-current="page"' if active=='lectures' else '')+f'>강의</a><a href="{base}concepts.html"'+(' aria-current="page"' if active=='concepts' else '')+f'>용어와 개념</a><a href="{base}mini-courses/index.html"'+(' aria-current="page"' if active=='courses' else '')+f'>미니강좌</a></nav></div></header>'
def footer(base='',account=False):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>{SITE_NAME}</span><a href="{base}index.html">자료 모음으로</a><a href="{base}concepts.html">용어와 개념</a><button type="button" class="theme-toggle" data-theme-toggle aria-label="화면 테마 변경">화면 · 시스템</button></div></footer>'
def page(title,body,base='',active=None,account=False):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#f6f4ee"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="{SITE_NAME}"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="description" content="김주환 교수의 강의 핵심 요약, 주제별 타임라인과 학습 자료"><title>{html.escape(title + " · " + SITE_NAME if title else SITE_NAME)}</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" sizes="180x180" href="{base}assets/apple-touch-icon.png"><link rel="manifest" href="{base}manifest.webmanifest"><script src="{base}assets/theme.js?v={ASSET_VERSION}"></script><link rel="stylesheet" href="{base}assets/site.css?v={ASSET_VERSION}"><script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script></head><body>{header(base,active)}{body}{footer(base,account)}</body></html>'
def render(rows, materials=None, courses=None):
    materials = materials or []
    courses = courses or {}
    # Preserve registry order and never infer dates for undated material.
    latest = rows[0] if rows else None
    featured = ''
    if latest:
        url = f'lectures/{latest["id"]}.html#lecture-overview'
        question = html.escape(courses.get(latest['id'], {}).get('question', ''))
        featured = f'''
        <section class="home-feature" aria-labelledby="featured-title">
          <p class="home-feature-label">대표 강의</p>
          <h2 id="featured-title"><a href="{url}">{html.escape(latest['title'])}</a></h2>
          <p>{question}</p>
          <a class="home-feature-action" href="{url}">강의 본문 읽기</a>
        </section>'''

    chips = ['<button type="button" data-filter-for="search" data-value="">전체</button>']
    for tag in dict.fromkeys(row.get('filter_tag', row['tags'][0]) for row in rows + materials):
        label = html.escape(tag, quote=True)
        chips.append(f'<button type="button" data-filter-for="search" data-value="{label}">{label}</button>')

    entries = []
    type_names = {'book': '책', 'paper': '연구', 'article': '글', 'note': '학습 노트'}
    for row in rows + materials:
        kind = row.get('kind', 'lecture')
        if kind == 'lecture':
            url = f'lectures/{row["id"]}.html#lecture-overview'
            identity = f' data-video-id="{row["id"]}"'
            date = row.get('date')
            meta = f'<time datetime="{date}">{date.replace("-", ".")}</time>' if date else ''
        else:
            if kind not in type_names:
                raise ValueError('지원하지 않는 자료 유형: ' + kind)
            url = row['url']
            if not isinstance(url, str) or not url or url.startswith(('/', '#')) or ':' in url or '..' in url.split('/'):
                raise ValueError('자료 주소는 사이트 내부 상대 경로만 허용합니다')
            identity = ''
            meta = f'<span>{type_names[kind]}</span>'
        creator = html.escape(row.get('creator', ''))
        description = row.get('description', '')
        reading_note = row.get('reading_note', description)
        searchable = html.escape(' '.join([
            row['title'], description, row.get('creator', ''), row.get('filter_tag', ''), kind, *row['tags']
        ]), quote=True)
        entries.append(f'''
        <a class="lecture-row" data-kind="{kind}"{identity} data-creator="{creator}" data-search="{searchable}" href="{html.escape(url, quote=True)}">
          <h3>{html.escape(row['title'])}</h3>
          <p>{html.escape(reading_note)}</p>
          <div class="meta">{meta}<span>{creator}</span></div>
        </a>''')

    body = f'''<div class="site-shell"><main id="main" class="home-main">
      <h1>{SITE_NAME}</h1>
      {featured.strip()}
      <section id="lectures" aria-labelledby="recent-title">
        <div class="search-panel">
          <label for="search">강의 검색</label>
          <div class="search-controls">
            <input class="search" id="search" type="search" placeholder="주제, 강의 제목, 강연자 검색" data-filter-input="#lecture-list" data-count="count" data-empty="empty" data-noun="자료" data-persist-query="true">
            <button type="button" class="btn secondary" data-clear-for="search" hidden>초기화</button>
          </div>
          <div class="filter-chips" aria-label="주제 필터">{''.join(chips)}</div>
        </div>
        <div class="section-heading"><h2 id="recent-title">최근 강의</h2><p class="search-summary" id="count" aria-live="polite">{len(entries)}개 자료</p></div>
        <div id="lecture-list">{''.join(entries)}</div>
        <p class="empty" id="empty" hidden>검색 결과가 없습니다. 다른 검색어를 입력하거나 ‘전체’를 선택해 주세요.</p>
      </section>
      <nav class="study-links" aria-label="관련 학습 자료">
        <div><a href="concepts.html">용어와 개념</a><p>강의에서 나온 용어와 뜻을 찾아봅니다.</p></div>
        <div id="learning-route-title"><a href="mini-courses/index.html">미니강좌</a><p>여러 강의에 걸친 주제를 묶어 짧게 읽습니다.</p></div>
      </nav>
    </main></div>'''
    return page('', body, active='lectures')

def build(check=False):
    result=render(json.loads((R/'lectures.json').read_text(encoding='utf-8')),json.loads((R/'materials.json').read_text(encoding='utf-8')),json.loads((R/'data/mini_courses.json').read_text(encoding='utf-8')))
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
