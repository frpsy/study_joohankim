"""Generate three-tier lecture notes and separate mini courses from reviewed copy."""
from pathlib import Path
import html,json,sys
from build_library import page,R
from editorial_copy import effective_summaries
E=html.escape
def load(name):return json.loads((R/'data'/name).read_text(encoding='utf-8'))
def render(row,record,mini,summary):
 vid=row['id']; title=E(row['title']);miniurl=f'../mini-courses/{vid}.html'
 # A lecture may be indexed by a stable internal content key before its actual YouTube ID is verified.
 youtube_url=row.get('video_url') or (f'https://www.youtube.com/watch?v={vid}' if len(vid)==11 and all(c.isascii() and (c.isalnum() or c in '-_') for c in vid) else None)
 source_info=(f'<a href="{E(youtube_url,quote=True)}" target="_blank" rel="noopener">원본 영상 ↗</a>' if youtube_url else '<span>원본 영상 주소 확인 중</span>')
 aliases=set(record['aliases'])-{'lecture-overview','overview','lecture-comment','timeline'}
 old=''.join(f'<span id="{E(a)}" class="legacy-anchor" aria-hidden="true"></span>' for a in sorted(aliases))
 preview='\n'.join(record['timeline'].splitlines()[:3])
 paragraphs=''.join(f'<h3>{E(s["h"])}</h3>'+''.join(f'<p>{E(p)}</p>' for p in s['p']) for s in summary['sections'])
 sources=''.join(f'<li><a href="{E(s["url"],quote=True)}" target="_blank" rel="noopener">{E(s["label"])}</a></li>' for s in record['sources'])
 body=f'''<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">자료 모음</a><span>/</span><span>{title}</span></nav><main id="main" class="compact-lecture" data-layout="compact"><header class="summary-head"><span class="eyebrow">강의 노트</span><h1>{title}</h1><p class="meta">{E(row['duration'])} · {E(row.get("creator","출처 미기재"))} · {source_info}</p><div class="actions"><a class="btn" href="{miniurl}">미니강좌 읽기</a><a class="btn secondary" href="#lecture-comment">타임라인</a></div></header><section id="lecture-overview" class="lecture-section"><span id="overview"></span><h2>핵심 요약</h2><div class="summary-tier"><span class="eyebrow">01 · 한 문장</span><p class="summary-lead">{E(mini['lead'])}</p></div><div class="summary-tier"><h3>02 · 핵심 3가지</h3><ol class="summary-list">{''.join('<li>'+E(t)+'</li>' for t in mini['three'])}</ol></div><details class="summary-tier"><summary>03 · 5분 요약</summary>{old}{paragraphs}<p class="summary-note">{E(summary['note'])}</p><a href="../summaries/{vid}.html">5분 요약만 읽기 →</a></details></section><section id="lecture-comment" class="lecture-section"><span id="timeline"></span><h2>댓글용 타임라인</h2><div class="actions"><button id="copy" data-copy-target="comment" type="button">댓글용 타임라인 복사</button><span id="status" role="status" aria-live="polite"></span></div><pre class="timeline-teaser" aria-label="타임라인 첫 세 줄"><code>{E(preview)}</code></pre><details class="timeline-disclosure"><summary>전체 타임라인 보기</summary><pre id="comment" tabindex="0"><code>{E(record['timeline'])}</code></pre></details></section><details class="source-disclosure"><summary>원본과 참고 자료</summary><ul>{sources}</ul></details><nav class="summary-links" aria-label="학습 탐색"><a href="{miniurl}">미니강좌 →</a><a href="../index.html">자료 모음</a><a href="../concepts.html">용어와 개념</a></nav></main></div>'''
 lecture=page(row['title'],body,base='../')
 sections=''.join(f'<section id="lesson-{i}"><h2>{i:02d} · {E(s["h"])}</h2>'+''.join(f'<p>{E(p)}</p>' for p in s['p'])+'</section>' for i,s in enumerate(mini['sections'],1))
 body=f'''<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">자료 모음</a><span>/</span><a href="../lectures/{vid}.html">강의 노트</a><span>/</span><span>미니강좌</span></nav><main id="main"><article class="summary-page mini-course"><header class="summary-head"><span class="eyebrow">미니강좌 · 약 4분</span><h1>{E(mini['title'])}</h1><p class="meta">원강의: {title} · {E(row.get("creator","출처 미기재"))}</p></header><p class="summary-lead">{E(mini['lead'])}</p>{sections}<details class="course-question"><summary>{E(mini['question'])}</summary><p>{E(mini['answer'])}</p></details><p class="meta">원강의 기반 학습 해설 · [보충]은 추가 예시</p><nav class="summary-links" aria-label="학습 탐색"><a class="btn" href="../lectures/{vid}.html">핵심 요약</a><a class="btn secondary" href="../lectures/{vid}.html#lecture-comment">원본 타임라인</a><a class="btn secondary" href="../index.html">자료 모음</a></nav></article></main></div>'''
 return lecture,page(mini['title'],body,base='../')
def build(check=False):
 records=load('lecture_compact.json');minis=load('mini_courses.json');summaries=effective_summaries(R);issues=[]
 for row in json.loads((R/'lectures.json').read_text(encoding='utf-8')):
  vid=row['id'];outputs=render(row,records[vid],minis[vid],summaries[vid])
  for folder,content in zip(('lectures','mini-courses'),outputs):
   p=R/folder/f'{vid}.html'
   if check:
    if not p.exists() or p.read_text(encoding='utf-8')!=content:issues.append(str(p.relative_to(R)))
   else:p.parent.mkdir(exist_ok=True);p.write_text(content,encoding='utf-8')
 if check:print('FAIL: '+', '.join(issues) if issues else 'PASS: compact lectures and mini courses match source')
 return bool(issues)
if __name__=='__main__':sys.exit(build('--check' in sys.argv))
