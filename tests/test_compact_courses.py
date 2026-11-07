import unittest,json,sys,re,html
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from build_compact_lectures import build
from validate_site import validate
class CompactCourseChecks(unittest.TestCase):
 def test_timeline_text_is_preserved_and_copy_has_single_target(self):
  records=json.loads((R/'data/lecture_compact.json').read_text())
  for vid,record in records.items():
   source=(R/'lectures'/f'{vid}.html').read_text()
   if 'timeline' not in record:continue
   text=re.search(r'<pre id="comment"[^>]*><code>(.*?)</code></pre>',source,re.S).group(1)
   self.assertEqual(html.unescape(text),record['timeline'])
   self.assertEqual(source.count('id="comment"'),1)
   self.assertEqual(source.count('data-copy-target="comment"'),1)
   self.assertIn('<div class="timeline-box"><pre id="comment"><code>',source)
   self.assertNotIn('timeline-toggle',source)
   self.assertNotIn('<label class="timeline-box"',source)
   for gone in ('전체 타임스탬프 보기','timeline-teaser','timeline-disclosure'):
    self.assertNotIn(gone,source)
   self.assertIn(html.escape("\n".join(record["timeline"].splitlines()[:3])),source)
   self.assertNotIn('class="timeline-preview"',source)
   self.assertNotIn('<img ',source[source.index('<main id="main"'):])
 def test_only_kim_lectures_have_timestamps_others_have_detailed_summary(self):
  rows=json.loads((R/'lectures.json').read_text());records=json.loads((R/'data/lecture_compact.json').read_text())
  for row in rows:
   vid=row['id'];record=records[vid];source=(R/'lectures'/f'{vid}.html').read_text()
   if row.get('creator')=='김주환':
    self.assertIn('timeline',record,vid);self.assertIn('id="lecture-comment"',source,vid);self.assertNotIn('id="lecture-detail"',source,vid)
   else:
    self.assertNotIn('timeline',record,vid);self.assertNotIn('id="lecture-comment"',source,vid);self.assertNotIn('timeline-toggle',source,vid)
    self.assertIn('id="lecture-detail"',source,vid);self.assertGreaterEqual(len(record['detail']),5,vid)
    self.assertGreaterEqual(len(record['sources']),3,vid)
    for block in record['detail']:
     self.assertTrue(block['h'] and block['p'],vid)
     for text in block['p']:self.assertRegex(text,r'[.)]$',vid+': '+text[:30])
 def test_course_coverage_and_tiers(self):
  rows=json.loads((R/'lectures.json').read_text());courses=json.loads((R/'data/mini_courses.json').read_text())
  self.assertEqual({r['id'] for r in rows},set(courses))
  for vid,item in courses.items():
   self.assertEqual(len(item['three']),3)
   self.assertTrue(item['sections'])
   self.assertFalse(any(str(x).startswith(('핵심 원리:', '훈련의 구분:', '실천 방향:')) for x in item['three']),vid)
   self.assertTrue(item['question'] and item['answer'])
   self.assertTrue(all(str(x).endswith('다.') for x in item['three']),vid)
  self.assertFalse(build(check=True))
  self.assertEqual(validate(R),[])
