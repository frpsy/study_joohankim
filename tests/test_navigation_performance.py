import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]

class NavigationPerformanceContract(unittest.TestCase):
    def test_static_cache_and_accountless_runtime(self):
        worker = (R / "sw.js").read_text(encoding="utf-8")
        self.assertIn("url.origin !== root.origin", worker)
        self.assertIn("request.method !== 'GET'", worker)
        self.assertIn("'./offline.html'", worker)
        self.assertNotIn("concepts.html", worker)
        self.assertNotIn("mini-courses", worker)
        self.assertNotIn("study-history.html", worker)
        self.assertNotIn("studyUsers", worker)
        for removed in ("assets/firebase.js", "assets/account.js", "assets/progress.js", "assets/firebase-config.js", "study-history.html"):
            self.assertFalse((R / removed).exists(), removed)

    def test_removed_account_layout_css_does_not_return(self):
        css = (R / "assets/site.css").read_text(encoding="utf-8")
        self.assertNotIn(".hub-actions", css)
        self.assertNotIn("#settings-toggle", css)

    def test_header_and_cards_do_not_regress(self):
        css = (R / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn(".site-header{background:var(--paper);", css)
        self.assertIn(".lecture .read{margin-top:8px;", css)
        self.assertIn(".site-shell,.site-header-inner,.site-footer-inner{width:calc(100% - 32px);padding-left:0;padding-right:0}", css)

if __name__ == "__main__":
    unittest.main()
