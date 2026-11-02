"""Verified video source must not change the stable content URL key."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT_ID = "affirmation-20261101"
VIDEO_ID = "oD5-nTDCKPg"
URL = "https://www.youtube.com/watch?v=" + VIDEO_ID

class OriginalVideoSourceTest(unittest.TestCase):
    def test_official_url_and_stable_content_key(self):
        rows = json.loads((ROOT/"lectures.json").read_text(encoding="utf-8"))
        row = next(x for x in rows if x["id"] == CONTENT_ID)
        self.assertEqual(row["video_url"], URL)
        sources = json.loads((ROOT/"data/lecture_compact.json").read_text(encoding="utf-8"))[CONTENT_ID]["sources"]
        self.assertEqual(sources[0]["url"], URL)
        lecture = (ROOT/"lectures"/f"{CONTENT_ID}.html").read_text(encoding="utf-8")
        self.assertIn('href="'+URL+'"', lecture)
        self.assertNotIn('id="study-progress"', lecture)
        self.assertNotIn("원본 영상 주소 확인 중", lecture)
        self.assertNotIn("watch?v="+CONTENT_ID, lecture)
        home = (ROOT/"index.html").read_text(encoding="utf-8")
        self.assertIn('data-video-id="'+CONTENT_ID+'"', home)
        audit = json.loads((ROOT/"study-audits"/f"{CONTENT_ID}.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["source_video_id"], VIDEO_ID)
        self.assertTrue(audit["source_url_verified"])

if __name__ == "__main__":
    unittest.main()
