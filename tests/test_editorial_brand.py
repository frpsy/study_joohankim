"""Guard the shared site name, icon, titles and asset freshness on every public page."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
PAGES=[ROOT/'index.html',ROOT/'concepts.html',ROOT/'study-history.html']
for folder in ('lectures','mini-courses','summaries'):
    PAGES.extend(sorted((ROOT/folder).glob('*.html')))

class EditorialBrandContract(unittest.TestCase):
    def test_all_page_titles_and_wordmarks_use_the_new_brand(self):
        self.assertGreaterEqual(len(PAGES),21)
        for path in PAGES:
            with self.subTest(page=str(path.relative_to(ROOT))):
                html=path.read_text(encoding='utf-8')
                self.assertIn('<title>내면의 서재 · ',html)
                self.assertIn('<span class="brand-name">내면의 서재<small>강의 · 개념 · 복습</small></span>',html)
                self.assertRegex(html,r'<img class="brand-symbol"[^>]+alt=""')
                self.assertNotIn('내면을 공부하는 시간',html)
                asset_version='20261101-editorial-v7'
                self.assertIn('site.css?v='+asset_version,html)
                self.assertIn('site.js?v='+asset_version,html)
                self.assertEqual(len(re.findall(r'<h1(?:\s|>)',html)),1)

    def test_home_has_consistent_editorial_hierarchy_and_no_content_loss(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('읽고, 듣고, 연결하는<br class="hero-title-break"> 내면의 서재',html)
        self.assertIn('개인 학습 아카이브',html)
        self.assertIn('최근 정리한 강의',html)
        self.assertEqual(html.count('class="lecture"'),6)
        self.assertIn('data-creator="Andrew Huberman"',html)
        self.assertIn('data-creator="김주환"',html)
        self.assertEqual(html.count('id="settings-toggle"'),1)
        self.assertIn('class="footer-account-link" id="settings-toggle"',html)
        self.assertIn('class="site-footer-account"',html)
        self.assertNotIn('id="settings-toggle"',html.split('<main id="main">')[0])
        for marker in ('id="settings-toggle"','id="search"','id="learning-route-title"','id="account-action"'):
            self.assertIn(marker,html)

    def test_asset_and_manifest_versions_are_synchronized(self):
        import json
        manifest=json.loads((ROOT/'build-info.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['version'],'2026.11.02.2')
        self.assertIn("const CLIENT_VERSION='2026.11.02.2'",(ROOT/'assets/site.js').read_text(encoding='utf-8'))
        self.assertIn("const VERSION = '20261102-multi-source-v9'",(ROOT/'sw.js').read_text(encoding='utf-8'))
        builder=(ROOT/'scripts/build_library.py').read_text(encoding='utf-8')
        self.assertIn("SITE_NAME='내면의 서재'",builder)
        self.assertIn("ASSET_VERSION='20261101-editorial-v7'",builder)

if __name__=='__main__':
    unittest.main()
