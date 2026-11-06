"""Ensure all study leads are complete, concrete and consistent across pages."""
import json
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
from sys import path as syspath
syspath.insert(0, str(R/'scripts'))
from content_registry import effective_summaries


class KoreanLeads(unittest.TestCase):
    def test_all_one_sentence_leads_match_across_three_reading_depths(self):
        minis = json.loads((R/'data/mini_courses.json').read_text(encoding='utf-8'))
        summaries = effective_summaries(R)
        registry = json.loads((R/'lectures.json').read_text(encoding='utf-8'))
        self.assertEqual(set(minis), {r['id'] for r in registry})
        self.assertEqual(set(minis), set(summaries))
        for vid, record in minis.items():
            with self.subTest(lecture=vid):
                lead = record['lead']
                self.assertEqual(sum(lead.count(c) for c in '.!?'), 1)
                self.assertTrue(lead.endswith('다.'), vid)
                self.assertGreaterEqual(len(lead), 55, vid)
                self.assertLessEqual(len(lead), 170, vid)
                self.assertFalse(re.search(r'\s{2,}', lead), vid)
                self.assertEqual(lead, summaries[vid]['lead'], '5분 요약과 한 문장 핵심이 다름: '+vid)
                for folder in ('lectures',):
                    text = (R/folder/f'{vid}.html').read_text(encoding='utf-8')
                    self.assertIn(lead, text, '화면이 편집 원고와 다름: '+folder+'/'+vid)


if __name__ == '__main__':
    unittest.main()
