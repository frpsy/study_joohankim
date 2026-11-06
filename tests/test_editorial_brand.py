"""Guard the shared site name, icon, titles and asset freshness on every public page."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT/'index.html', *sorted((ROOT/'lectures').glob('*.html'))]

class EditorialBrandContract(unittest.TestCase):
    def test_all_page_titles_and_wordmarks_use_the_new_brand(self):
        self.assertGreaterEqual(len(PAGES), 8)
        from sys import path as py_path
        py_path.insert(0,str(ROOT/'scripts'))
        from build_library import ASSET_VERSION
        asset_version=ASSET_VERSION
        for path in PAGES:
            with self.subTest(page=str(path.relative_to(ROOT))):
                html = path.read_text(encoding='utf-8')
                self.assertIn('<title>내면의 서재 · ', html)
                self.assertIn('<span class="brand-name">내면의 서재<small>강의 요약 · 타임스탬프</small></span>', html)
                self.assertRegex(html, r'<img class="brand-symbol"[^>]+alt=""')
                self.assertNotIn('내면을 공부하는 시간', html)
                self.assertIn('site.css?v='+asset_version, html)
                self.assertIn('site.js?v='+asset_version, html)
                self.assertEqual(len(re.findall(r'<h1(?:\s|>)', html)), 1)

    def test_home_has_consistent_editorial_hierarchy_and_no_content_loss(self):
        html = (ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('<h1 class="home-title">강의 요약</h1>', html)
        self.assertNotIn('개인 학습 아카이브', html)
        self.assertNotIn('나의 학습 자료', html)
        expected = len(json.loads((ROOT/'lectures.json').read_text(encoding='utf-8')))
        expected += len(json.loads((ROOT/'materials.json').read_text(encoding='utf-8')))
        self.assertEqual(html.count('data-kind='), expected)
        self.assertEqual(html.count('class="home-feature"'), 0)
        self.assertEqual(html.count('data-video-id="affirmation-20261101"'), 1)
        self.assertNotIn('<h1>내면의 서재</h1>', html)
        self.assertIn('data-filter-input="#home-catalog"', html)
        self.assertIn('href="lectures/affirmation-20261101.html"', html)
        self.assertIn('data-creator="Andrew Huberman"', html)
        self.assertIn('data-creator="김주환"', html)
        self.assertNotIn('study-history.html', html)
        self.assertNotIn('id="settings-toggle"', html)
        self.assertNotIn('id="account-action"', html)
        self.assertIn('id="search"', html)
        for removed in ('id="learning-route-title"', 'concepts.html', 'mini-courses/'):
            self.assertNotIn(removed, html)
        self.assertNotIn('class="hero-description"', html)
        self.assertNotIn('class="learning-flow"', html)

    def test_asset_and_manifest_versions_are_synchronized(self):
        manifest = json.loads((ROOT/'build-info.json').read_text(encoding='utf-8'))
        self.assertRegex(manifest['version'], r'^\d{4}\.\d{2}\.\d{2}\.\d+$')
        script = (ROOT/'assets/site.js').read_text(encoding='utf-8')
        self.assertIn("new URL(siteScriptURL).searchParams.get('v')", script)
        self.assertIn("workerURL.searchParams.set('v'", script)
        worker = (ROOT/'sw.js').read_text(encoding='utf-8')
        self.assertIn("new URL(self.location.href).searchParams.get('v')", worker)
        from build_library import ASSET_VERSION
        self.assertEqual(ASSET_VERSION, manifest['version'])

if __name__ == '__main__':
    unittest.main()
