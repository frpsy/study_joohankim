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


class WordingRegression(unittest.TestCase):
    BANNED = ("자막은 ", "자막 없음", "소개란 없음", "영어를 병기", "화면 화면", "교수의 해석")

    def test_public_pages_have_no_production_notes(self):
        root = Path(__file__).resolve().parents[1]
        pages = [root / "index.html", root / "concepts.html", *sorted((root / "lectures").glob("*.html"))]
        for page in pages:
            text = page.read_text(encoding="utf-8")
            for word in self.BANNED:
                self.assertNotIn(word, text, f"{page.name}: {word}")

class TimelineDisplayRegression(unittest.TestCase):
    def test_no_separate_timeline_link_lists(self):
        import re
        root=Path(__file__).resolve().parents[1]
        for page in (root/'lectures').glob('*.html'):
            source=page.read_text(encoding='utf-8')
            sections=re.findall(r'<section[^>]*id="(?:lecture-comment|timeline|comment|comment-section)"[^>]*>.*?</section>',source,re.S)
            self.assertTrue(any('<pre' in section for section in sections),page.name)
            for section in sections:
                self.assertNotRegex(section,r'<(?:ol|ul)\b',page.name)

class LectureLayoutRegression(unittest.TestCase):
    def test_missing_required_stage_is_rejected(self):
        from validate_site import lecture_layout_errors
        root=Path(__file__).resolve().parents[1]
        source=(root/'lectures/ZCty0wvogDo.html').read_text()
        self.assertEqual(lecture_layout_errors(source),[])
        self.assertIn('standard lecture section missing',lecture_layout_errors(source.replace('id="lecture-review"','id="missing-review"')))

    def test_copy_status_must_be_announced(self):
        from validate_site import lecture_layout_errors
        root=Path(__file__).resolve().parents[1]
        source=(root/'lectures/ZCty0wvogDo.html').read_text()
        self.assertIn('accessible copy status missing',lecture_layout_errors(source.replace('aria-live="polite"','')))

class MindmapRegression(unittest.TestCase):
    def test_outline_changes_require_regeneration(self):
        import shutil
        from build_mindmaps import errors
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            shutil.copytree(repo/'lectures',root/'lectures')
            shutil.copytree(repo/'data',root/'data')
            shutil.copyfile(repo/'lectures.json',root/'lectures.json')
            self.assertEqual(errors(root),[])
            path=root/'data/lecture_mindmaps.json'
            outlines=json.loads(path.read_text())
            first=next(iter(outlines));outlines[first]['root']='새 중심 개념'
            path.write_text(json.dumps(outlines,ensure_ascii=False))
            self.assertIn('generated mindmap differs: '+first,errors(root))
