import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]

class NavigationPerformanceContract(unittest.TestCase):
    def test_public_cache_scope_never_includes_firebase_data(self):
        worker = (R / "sw.js").read_text(encoding="utf-8")
        self.assertIn("url.origin !== root.origin", worker)
        self.assertIn("request.method !== 'GET'", worker)
        self.assertIn("request.mode === 'navigate'", worker)
        self.assertIn("'./concepts.html'", worker)
        self.assertIn("'./study-history.html'", worker)
        self.assertNotIn("firestore.googleapis.com", worker)
        self.assertNotIn("studyUsers", worker)

    def test_no_firestore_download_for_unauthed_navigation(self):
        sdk = (R / "assets/firebase.js").read_text(encoding="utf-8")
        self.assertIn("function authInstance()", sdk)
        self.assertIn("function dbInstance()", sdk)
        self.assertNotIn("Promise.all([\n      import", sdk)
        progress = (R / "assets/progress.js").read_text(encoding="utf-8")
        self.assertLess(progress.index("async function renderSignedIn("), progress.index("await getDb()"))
        home = (R / "assets/account.js").read_text(encoding="utf-8")
        self.assertIn("requestIdleCallback(ensureAuth", home)
        self.assertIn("if (open) {\n    ensureAuth();", home)

    def test_header_and_cards_do_not_regress(self):
        css = (R / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn(".site-header{background:var(--paper);", css)
        self.assertIn(".lecture .read{margin-top:8px;", css)
        self.assertIn(".site-shell,.site-header-inner,.site-footer-inner{width:calc(100% - 32px);padding-left:0;padding-right:0}", css)

if __name__ == "__main__":
    unittest.main()
