import sys,unittest,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_site import structural_errors,validate
from build_library import render
BASE='<link rel="stylesheet" href="assets/site.css"><script src="assets/site.js"></script><header class="site-header"></header><main id="main"><h1>학습</h1></main>'
class DesignRegression(unittest.TestCase):
    def test_common_layout(self):self.assertEqual(structural_errors(BASE)[0],[])
    def test_missing_shared_css(self):self.assertIn('shared stylesheet missing',structural_errors(BASE.replace('assets/site.css','old.css'))[0])
    def test_note_ui_regression(self):self.assertIn('removed note UI reintroduced',structural_errors(BASE+'<textarea id="note"></textarea>')[0])
    def test_duplicate_heading(self):self.assertIn('expected one page title',structural_errors(BASE+'<h1>둘</h1>')[0])
    def test_inline_style_regression(self):self.assertIn('page-specific inline style reintroduced',structural_errors(BASE+'<p style="color:red">x</p>')[0])
    def test_broken_cross_page_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'assets').mkdir();(root/'assets/site.css').write_text('');(root/'assets/site.js').write_text('')
            (root/'lectures.json').write_text('[]',encoding='utf-8');(root/'index.html').write_text(BASE+'<a href="missing.html">잘못된 이동</a>',encoding='utf-8');(root/'concepts.html').write_text(BASE,encoding='utf-8')
            self.assertTrue(any('missing target missing.html' in x for x in validate(root)))

class GeneratorRegression(unittest.TestCase):
    def test_registry_drives_new_topic_and_escapes_text(self):
        row={'id':'example','date':None,'title':'A < B & C','duration':'1분','description':'<em>문장</em>','tags':['새 주제']}
        source=render([row])
        self.assertIn('data-value="새 주제"',source)
        self.assertIn('A &lt; B &amp; C',source)
        self.assertNotIn('<em>문장</em>',source)
        self.assertIn('1개 강의',source)
        self.assertNotIn('<time',source)

    def test_hand_edited_home_is_rejected(self):
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            repo=Path(__file__).resolve().parents[1]
            for name in ('assets','lectures'):
                shutil.copytree(repo/name,root/name)
            for name in ('index.html','concepts.html','lectures.json'):
                shutil.copyfile(repo/name,root/name)
            home=root/'index.html'
            home.write_text(home.read_text().replace('나의 강의 학습 노트','임의로 바꾼 제목'))
            self.assertIn('generated home differs from index.html',validate(root))

if __name__=='__main__':unittest.main()
