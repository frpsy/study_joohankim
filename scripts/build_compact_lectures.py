"""Generate three-tier lecture notes and separate mini courses from reviewed copy."""
from pathlib import Path
import html,json,re,sys
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from build_library import page,R
from content_registry import effective_summaries
E=html.escape
def load(name):return json.loads((R/'data'/name).read_text(encoding='utf-8'))
def detailed_timeline(text, video_url):
    """Render the existing detailed chapter text as timestamp links."""
    _, _, details = text.partition('—상세—')
    groups = []
    for line in details.splitlines():
        if line.startswith('■ '):
            groups.append((line[2:], []))
        elif groups and (match := re.fullmatch(r'(\d+:\d{2}(?::\d{2})?) (.+)', line)):
            stamp, label = match.groups()
            seconds = 0
            for part in stamp.split(':'):
                seconds = seconds * 60 + int(part)
            entry = f'<span class="timeline-stamp">{stamp}</span> {E(label)}'
            if video_url:
                url = urlsplit(video_url)
                query = dict(parse_qsl(url.query))
                query['t'] = seconds
                href = E(urlunsplit(url._replace(query=urlencode(query))), quote=True)
                entry = f'<a href="{href}" target="_blank" rel="noopener">{entry}</a>'
            groups[-1][1].append(f'<li>{entry}</li>')
    return ''.join(f'<h3>{E(title)}</h3><ul>{"".join(entries)}</ul>' for title, entries in groups)

def render(row,record,mini,summary):
 vid=row['id']; title=E(row['title']);miniurl=f'../mini-courses/{vid}.html'
 # A lecture may be indexed by a stable internal content key before its actual YouTube ID is verified.
 youtube_url=row.get('video_url') or (f'https://www.youtube.com/watch?v={vid}' if len(vid)==11 and all(c.isascii() and (c.isalnum() or c in '-_') for c in vid) else None)
 source_info=(f'<a href="{E(youtube_url,quote=True)}" target="_blank" rel="noopener">원본 영상 ↗</a>' if youtube_url else '<span>원본 영상 주소 확인 중</span>')
 aliases=set(record['aliases'])-{'lecture-overview','overview','lecture-details','details','lecture-comment','timeline'}
 old=''.join(f'<span id="{E(a)}" class="legacy-anchor" aria-hidden="true"></span>' for a in sorted(aliases))
 preview='\n'.join(f'<span>{E(line)}</span>' for line in record['timeline'].splitlines()[:3])
 detail_items=detailed_timeline(record['timeline'], youtube_url)
 detail_alias='<span id="details"></span>' if 'details' in record['aliases'] else ''
 caption=E(row.get('caption_label', ''))
 paragraphs=''.join(f'<h3>{E(s["h"])}</h3>'+''.join(f'<p>{E(p)}</p>' for p in s['p']) for s in summary['sections'])
 sources=''.join(f'<li><a href="{E(s["url"],quote=True)}" target="_blank" rel="noopener">{E(s["label"])}</a></li>' for s in record['sources'])
 body=f'''<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">자료 모음</a><span>/</span><span>{title}</span></nav><main id="main" class="compact-lecture" data-layout="compact"><header class="summary-head"><h1>{title}</h1><p class="meta">{E(row['duration'])} · {E(row.get("creator","출처 미기재"))} · {source_info}</p></header><section id="lecture-overview" class="lecture-section"><span id="overview"></span><h2>핵심 요약</h2><div class="summary-tier"><span class="eyebrow">01 · 한 문장</span><p class="summary-lead">{E(mini['lead'])}</p></div><div class="summary-tier"><h3>02 · 핵심 3가지</h3><ol class="summary-list">{''.join('<li>'+E(t)+'</li>' for t in mini['three'])}</ol></div><details class="summary-tier"><summary>03 · 5분 요약</summary>{old}{paragraphs}<p class="summary-note">{E(summary['note'])}</p><a href="../summaries/{vid}.html">5분 요약만 읽기 →</a></details></section>
 <section id="lecture-details" class="lecture-section"><h2>주제별 상세 타임라인</h2><details class="topic-timeline"><summary>주제와 시간 보기</summary>{detail_alias}{detail_items}</details></section>
 <section id="lecture-comment" class="lecture-section"><span id="timeline"></span><h2>유튜브 댓글용 타임라인</h2><p class="meta">{caption}</p><div class="actions"><button id="copy" data-copy-target="comment" type="button" aria-label="댓글용 타임라인 복사">복사</button><span id="status" role="status" aria-live="polite"></span></div><details class="timeline-disclosure"><summary><span class="when-closed">펼치기</span><span class="when-open">접기</span></summary><pre id="comment" tabindex="0"><code>{E(record['timeline'])}</code></pre></details><pre class="timeline-teaser" aria-label="타임라인 첫 세 줄"><code>{preview}</code></pre></section><details class="source-disclosure"><summary>원본과 참고 자료</summary><ul>{sources}</ul></details><nav class="summary-links" aria-label="학습 탐색"><a href="{miniurl}">미니강좌 →</a><a href="../index.html">자료 모음</a><a href="../concepts.html">용어와 개념</a></nav></main></div>'''
 lecture=page(row['title'],body,base='../')
 sections=''.join(f'<section id="lesson-{i}"><h2>{i:02d} · {E(s["h"])}</h2>'+''.join(f'<p>{E(p)}</p>' for p in s['p'])+'</section>' for i,s in enumerate(mini['sections'],1))
 body=f'''<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">자료 모음</a><span>/</span><a href="../lectures/{vid}.html">강의 노트</a><span>/</span><span>미니강좌</span></nav><main id="main"><article class="summary-page mini-course"><header class="summary-head"><span class="eyebrow">미니강좌 · 약 4분</span><h1>{E(mini['title'])}</h1><p class="meta">원강의: {title} · {E(row.get("creator","출처 미기재"))}</p></header><p class="summary-lead">{E(mini['lead'])}</p>{sections}<details class="course-question"><summary>{E(mini['question'])}</summary><p>{E(mini['answer'])}</p></details><p class="meta">원강의 기반 학습 해설 · [보충]은 추가 예시</p><nav class="summary-links" aria-label="학습 탐색"><a class="btn" href="../lectures/{vid}.html">핵심 요약</a><a class="btn secondary" href="../lectures/{vid}.html#lecture-comment">원본 타임라인</a><a class="btn secondary" href="../index.html">자료 모음</a></nav></article></main></div>'''
 return lecture,page(mini['title'],body,base='../')
COURSE_TOPICS = {
    '감정과 관계': ('xA-4G4z-1MM', 'ZCty0wvogDo', 'hw4_kLaHOMg'),
    '기억과 자기 대화': ('izYj8g-j00U', 'affirmation-20261101'),
    '명상과 동기': ('vHuZh8xLcDc', 'QmOF0crdyRU'),
}

def render_course_index(courses):
    def course_links(ids):
        return ''.join(f'<li><a href="{vid}.html">{E(courses[vid]["title"])}</a></li>' for vid in ids)

    grouped = set()
    sections = []
    for topic, ids in COURSE_TOPICS.items():
        available = [vid for vid in ids if vid in courses]
        if available:
            sections.append(f'<section><h2>{topic}</h2><ul>{course_links(available)}</ul></section>')
            grouped.update(available)
    remaining = [vid for vid in courses if vid not in grouped]
    if remaining:
        sections.append(f'<section><h2>다른 주제</h2><ul>{course_links(remaining)}</ul></section>')
    body = f'''<div class="site-shell"><main id="main" class="course-index">
      <h1>미니강좌</h1><p>여러 강의에 걸친 주제를 묶어 짧게 읽습니다.</p>
      {''.join(sections)}
    </main></div>'''
    return page('미니강좌', body, base='../', active='courses')

def build(check=False):
 records=load('lecture_compact.json');minis=load('mini_courses.json');summaries=effective_summaries(R);issues=[]
 for row in json.loads((R/'lectures.json').read_text(encoding='utf-8')):
  vid=row['id'];outputs=render(row,records[vid],minis[vid],summaries[vid])
  for folder,content in zip(('lectures','mini-courses'),outputs):
   p=R/folder/f'{vid}.html'
   if check:
    if not p.exists() or p.read_text(encoding='utf-8')!=content:issues.append(str(p.relative_to(R)))
   else:p.parent.mkdir(exist_ok=True);p.write_text(content,encoding='utf-8')
 index=R/'mini-courses/index.html'
 index_html=render_course_index(minis)
 if check:
  if not index.exists() or index.read_text(encoding='utf-8')!=index_html:issues.append(str(index.relative_to(R)))
 else:index.write_text(index_html,encoding='utf-8')
 if check:print('FAIL: '+', '.join(issues) if issues else 'PASS: compact lectures and mini courses match source')
 return bool(issues)
if __name__=='__main__':sys.exit(build('--check' in sys.argv))
