"""Guard the shared site name, icon, titles and asset freshness on every public page."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT/'index.html', ROOT/'concepts.html']
for folder in ('lectures', 'mini-courses', 'summaries'):
    PAGES.extend(sorted((ROOT/folder).glob('*.html')))

class EditorialBrandContract(unittest.TestCase):
    def test_all_page_titles_and_wordmarks_use_the_new_brand(self):
        self.assertGreaterEqual(len(PAGES), 21)
        builder = (ROOT/'scripts/build_library.py').read_text(encoding='utf-8')
        asset_version = re.search(r"ASSET_VERSION='([^']+)'", builder).group(1)
        for path in PAGES:
            with self.subTest(page=str(path.relative_to(ROOT))):
                html = path.read_text(encoding='utf-8')
                self.assertIn('<title>내면의 서재 · ', html)
                self.assertIn('<span class="brand-name">내면의 서재<small>강의 · 개념 · 미니강좌</small></span>', html)
                self.assertRegex(html, r'<img class="brand-symbol"[^>]+alt=""')
                self.assertNotIn('내면을 공부하는 시간', html)
                self.assertIn('site.css?v='+asset_version, html)
                self.assertIn('site.js?v='+asset_version, html)
                self.assertEqual(len(re.findall(r'<h1(?:\s|>)', html)), 1)

    def test_home_has_consistent_editorial_hierarchy_and_no_content_loss(self):
        html = (ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('<h1>학습 자료</h1>', html)
        self.assertNotIn('개인 학습 아카이브', html)
        self.assertNotIn('나의 학습 자료', html)
        self.assertIn('대표 강의', html)
        expected = len(json.loads((ROOT/'lectures.json').read_text(encoding='utf-8')))
        expected += len(json.loads((ROOT/'materials.json').read_text(encoding='utf-8')))
        self.assertEqual(html.count('data-kind='), expected)
        self.assertEqual(html.count('class="home-feature"'), 1)
        self.assertEqual(html.count('data-video-id="affirmation-20261101"'), 1)
        self.assertNotIn('<h1>내면의 서재</h1>', html)
        self.assertIn('data-filter-input="#home-catalog"', html)
        self.assertIn('href="lectures/affirmation-20261101.html"><span class="eyebrow">대표 강의</span>', html)
        self.assertIn('data-creator="Andrew Huberman"', html)
        self.assertIn('data-creator="김주환"', html)
        self.assertNotIn('study-history.html', html)
        self.assertNotIn('id="settings-toggle"', html)
        self.assertNotIn('id="account-action"', html)
        for marker in ('id="search"', 'id="learning-route-title"'):
            self.assertIn(marker, html)
        self.assertNotIn('class="hero-description"', html)
        self.assertNotIn('class="learning-flow"', html)

    def test_asset_and_manifest_versions_are_synchronized(self):
        manifest = json.loads((ROOT/'build-info.json').read_text(encoding='utf-8'))
        self.assertRegex(manifest['version'], r'^\d{4}\.\d{2}\.\d{2}\.\d+$')
        script = (ROOT/'assets/site.js').read_text(encoding='utf-8')
        self.assertIn("const CLIENT_VERSION='"+manifest['version']+"'", script)
        worker = (ROOT/'sw.js').read_text(encoding='utf-8')
        self.assertRegex(worker, r"const VERSION = '[^']+'")
        builder = (ROOT/'scripts/build_library.py').read_text(encoding='utf-8')
        self.assertIn("SITE_NAME='내면의 서재'", builder)
        self.assertRegex(builder, r"ASSET_VERSION='[^']+'")

if __name__ == '__main__':
    unittest.main()
