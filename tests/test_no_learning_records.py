"""Prevent reintroduction of account, completion, and learning-history features."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class NoLearningRecordFeatures(unittest.TestCase):
    def test_deleted_modules_absent(self):
        for path in ("study-history.html","assets/progress.js","assets/account.js","assets/firebase.js","assets/firebase-config.js"):
            with self.subTest(path=path):self.assertFalse((ROOT/path).exists())
    def test_no_account_or_record_navigation_in_pages(self):
        pages=[ROOT/"index.html"]
        for folder in ("lectures",):pages.extend((ROOT/folder).glob("*.html"))
        for path in pages:
            with self.subTest(path=str(path.relative_to(ROOT))):
                html=path.read_text(encoding="utf-8")
                for token in ("study-history.html","assets/progress.js","assets/account.js",'id="study-progress"','id="settings-toggle"','id="account-action"','학습 완료','복습 완료'):
                    self.assertNotIn(token,html)
    def test_cache_and_runtime_never_load_auth_or_history(self):
        worker=(ROOT/"sw.js").read_text(encoding="utf-8")
        self.assertNotIn("study-history.html",worker)
        builder=(ROOT/"scripts/build_library.py").read_text(encoding="utf-8")
        self.assertNotIn("study-history.html",builder)
        self.assertNotIn("assets/account.js",builder)
        lecture=(ROOT/"scripts/build_compact_lectures.py").read_text(encoding="utf-8")
        self.assertNotIn("assets/progress.js",lecture)
        self.assertNotIn("study-progress",lecture)

if __name__=="__main__":unittest.main()
