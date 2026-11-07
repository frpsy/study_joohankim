"""Contract checks for iPhone Home Screen web app and desktop bookmark reading."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class IPhonePWAContract(unittest.TestCase):
    def test_manifest_is_scoped_to_repo_and_uses_existing_icons(self):
        data=json.loads((ROOT/'manifest.webmanifest').read_text(encoding='utf-8'))
        self.assertEqual(data['id'],'/study_joohankim/')
        self.assertEqual(data['start_url'],'./index.html')
        self.assertEqual(data['scope'],'./')
        self.assertEqual(data['display'],'standalone')
        self.assertEqual(data['lang'],'ko-KR')
        for icon in data['icons']:
            path=ROOT/icon['src'].removeprefix('./')
            self.assertTrue(path.is_file(),str(path))
            self.assertGreater(path.stat().st_size,100)
        self.assertFalse((ROOT/'ios').exists())

    def test_iphone_and_desktop_pages_share_app_theme(self):
        self.assertEqual(len(list((ROOT/'lectures').glob('*.html'))),9)
        pages=[ROOT/'index.html',ROOT/'offline.html']+sorted((ROOT/'lectures').glob('*.html'))
        for page in pages:
            with self.subTest(path=str(page.relative_to(ROOT))):
                html=page.read_text(encoding='utf-8')
                self.assertIn('rel="manifest"',html)
                self.assertIn('viewport-fit=cover',html)
                self.assertIn('meta name="theme-color"',html)
                self.assertIn('apple-mobile-web-app-capable',html)
                self.assertIn('data-theme-toggle',html)
                self.assertIn('assets/theme.js',html)
                self.assertNotIn('assets/firebase.js',html)
                self.assertNotIn('study-history.html',html)
                self.assertNotIn('id="study-progress"',html)

    def test_system_theme_and_offline_library_are_available(self):
        js=(ROOT/'assets/theme.js').read_text(encoding='utf-8')
        css=(ROOT/'assets/site.css').read_text(encoding='utf-8')
        sw=(ROOT/'sw.js').read_text(encoding='utf-8')
        self.assertIn('prefers-color-scheme: dark',js)
        self.assertIn("modes=['auto','light','dark']",js)
        self.assertIn('localStorage',js)
        self.assertIn(':root[data-theme="dark"]',css)
        self.assertIn('env(safe-area-inset-top',css)
        self.assertIn('manifest.webmanifest',sw)
        self.assertIn('offline.html',sw)
        self.assertIn("'./lectures/'+row.id+'.html'",sw)
        self.assertNotIn('mini-courses',sw)
        self.assertNotIn('studyUsers',sw)
        self.assertNotIn('assets/progress.js',sw)
        self.assertNotIn('assets/account.js',sw)

if __name__=='__main__':unittest.main()
