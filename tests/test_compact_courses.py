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
   text=re.search(r'<pre id="comment"[^>]*><code>(.*?)</code></pre>',source,re.S).group(1)
   self.assertEqual(html.unescape(text),record['timeline'])
   self.assertEqual(source.count('id="comment"'),1)
   self.assertEqual(source.count('data-copy-target="comment"'),1)
   self.assertNotIn('<img ',source)
 def test_course_coverage_and_tiers(self):
  rows=json.loads((R/'lectures.json').read_text());courses=json.loads((R/'data/mini_courses.json').read_text())
  self.assertEqual({r['id'] for r in rows},set(courses))
  for vid,item in courses.items():
   self.assertEqual(len(item['three']),3)
   self.assertTrue(item['sections'])
   self.assertTrue(item['question'] and item['answer'])
   self.assertIn('원강의를 바탕으로 논지를 재구성한 학습 해설', (R/'mini-courses'/f'{vid}.html').read_text())
  self.assertFalse(build(check=True))
  self.assertEqual(validate(R),[])
