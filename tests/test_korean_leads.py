import json,re,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class KoreanLeads(unittest.TestCase):
 def test_all_one_sentence_leads(self):
  data=json.loads((R/'data/mini_courses.json').read_text())
  for vid,record in data.items():
   lead=record['lead']
   self.assertEqual(len(re.findall(r'[.!?](?=\\s|$)',lead)),1,vid)
   self.assertTrue(lead.endswith('다.'),vid)
   for folder in ('lectures','mini-courses'):
    self.assertIn(lead,(R/folder/f'{vid}.html').read_text(),vid)
if __name__=='__main__':unittest.main()
