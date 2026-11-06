"""기존 색상·공통 상호작용을 다른 AI가 실수로 바꾸지 못하도록 검사."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_pr_impact import impact_errors
from validate_design_system import contract_errors, TOKENS


class DesignContractRegression(unittest.TestCase):
    def test_current_site_matches_design_contract(self):
        self.assertEqual(contract_errors(ROOT), [])

    def test_canonical_tokens_cover_type_color_spacing_and_tap(self):
        for name in ("--paper", "--accent", "--font-body-size", "--space-4", "--radius-control", "--tap-target"):
            self.assertIn(name, TOKENS)

    def test_incomplete_pr_impact_is_rejected(self):
        body = "## 변경 범위\n작업 수정\n## 영향 기능\n테스트 확인"
        errors = impact_errors(body)
        self.assertTrue(any("남은 위험" in error for error in errors))
        self.assertTrue(any("검증 증거" in error for error in errors))

    def test_substantive_pr_impact_is_accepted(self):
        body = (
            "## 변경 범위\n공통 디자인 토큰과 정적 검증기 추가\n"
            "## 영향 기능\n홈과 강의의 디자인 기준만 정리하고 기존 데이터 보존\n"
            "## 검증 증거\n파이썬 및 노드 검사를 실행하여 변경 범위를 확인\n"
            "## 남은 위험\n실물 아이폰 Safari는 이번 변경에서 직접 확인하지 못함\n"
        )
        self.assertEqual(impact_errors(body), [])


if __name__ == "__main__":
    unittest.main()
