"""Regression contracts for canonical summaries and catalog source records."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from content_registry import effective_summaries, validate_catalog, load_json


class CanonicalContentRegression(unittest.TestCase):
    def test_all_seven_source_leads_match_generated_summaries(self):
        courses=load_json(ROOT/"data/mini_courses.json")
        summaries=load_json(ROOT/"data/summaries.json")
        combined=effective_summaries(ROOT)
        self.assertEqual(len(combined),len(courses))
        self.assertEqual(set(combined),set(summaries))
        for vid,course in courses.items():
            with self.subTest(lecture=vid):
                self.assertNotIn("lead",summaries[vid], "duplicate takeaway source")
                self.assertEqual(combined[vid]["lead"],course["lead"])
                self.assertIn(course["lead"],(ROOT/"lectures"/f"{vid}.html").read_text(encoding="utf-8"))

    def test_mismatched_and_missing_source_data_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"data").mkdir()
            (root/"data/summaries.json").write_text(json.dumps({"one":{"sections":[],"lead":"incorrect"}}),encoding="utf-8")
            (root/"data/mini_courses.json").write_text(json.dumps({"one":{"lead":"correct"}}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Conflicting"):effective_summaries(root)
            (root/"data/mini_courses.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"coverage"):effective_summaries(root)

    def test_catalog_has_unique_ids_and_required_metadata(self):
        self.assertEqual(validate_catalog(ROOT),[])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            row={"id":"duplicate","title":"Test","creator":"Speaker","description":"Description","tags":["topic"]}
            (root/"lectures.json").write_text(json.dumps([row]),encoding="utf-8")
            (root/"materials.json").write_text(json.dumps([{**row,"kind":"book","url":"books/one.html"}]),encoding="utf-8")
            self.assertIn("Duplicate stable content ID in registry",validate_catalog(root))


if __name__=="__main__":
    unittest.main()
