import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_study_pages import inspect

PAGE='<section id="overview"></section><a href="#overview">목차</a><div data-study-unit="one"><details><summary data-check="question">왜?</summary><p data-check="answer">이유를 설명한 답</p></details></div><img src="a.jpg" alt="화면">'
LEDGER={'video_id':'example','image_count':1,'units':[{'id':'one','source_start':1,'source_end':10,'slides':['overview']}]}
class ValidationRegression(unittest.TestCase):
    def test_valid(self):self.assertEqual(inspect(PAGE,LEDGER,20),[])
    def test_broken_anchor(self):self.assertTrue(any('broken anchor' in x for x in inspect(PAGE.replace('href="#overview"','href="#missing"'),LEDGER,20)))
    def test_empty_answer(self):self.assertTrue(any('missing answer' in x for x in inspect(PAGE.replace('이유를 설명한 답',' '),LEDGER,20)))
    def test_missing_image(self):self.assertTrue(any('image count' in x for x in inspect(PAGE.replace('<img src="a.jpg" alt="화면">',''),LEDGER,20)))
    def test_wrong_unit(self):self.assertTrue(any('ledger differ' in x for x in inspect(PAGE.replace('data-study-unit="one"','data-study-unit="two"'),LEDGER,20)))
    def test_bad_range(self):self.assertTrue(any('range out of bounds' in x for x in inspect(PAGE,LEDGER,5)))
    def test_duplicate_id(self):self.assertTrue(any('duplicate id' in x for x in inspect(PAGE+'<p id="overview"></p>',LEDGER,20)))
if __name__=='__main__':unittest.main()
