"""디자인 토큰 및 댓글 복사 동작의 공통 계약을 검사한다."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TOKENS = {
    "--paper": "#f6f4ee",
    "--surface": "#fffefa",
    "--ink": "#253c33",
    "--muted": "#5f7167",
    "--line": "#d9ded2",
    "--green": "#315b46",
    "--tint": "#e8eedf",
    "--radius": "16px",
    "--radius-card": "var(--radius)",
    "--radius-control": "9px",
    "--font-body-size": "17px",
    "--font-ui-size": "14px",
    "--line-height-body": "1.85",
    "--space-1": "4px", "--space-2": "8px", "--space-3": "12px",
    "--space-4": "16px", "--space-5": "20px", "--space-6": "24px",
    "--space-8": "32px", "--space-12": "48px",
    "--site-max-width": "1160px",
    "--tap-target": "44px",
    "--button-pad-y": "9px", "--button-pad-x": "15px",
    "--brand-ink": "#213b30",
    "--brand-soft": "#edf2e9",
    "--brand-outline": "#dbe5da",
    "--reading-measure": "720px",
    "--card-shadow": "0 2px 12px rgba(32,55,43,.035)",
}
CSS_CONTRACT = (
    "font:var(--font-body-size)/var(--line-height-body)",
    "width:min(var(--site-max-width),",
    "border-radius:var(--radius-control);padding:var(--button-pad-y) var(--button-pad-x)",
    "min-height:var(--tap-target)",
    ".lecture-section pre{",
    "white-space:pre-wrap;overflow-wrap:anywhere",
    "@media(max-width:780px)",
)
JS_CONTRACT = (
    "document.querySelectorAll('[data-copy-target]')",
    "navigator.clipboard.writeText(source.textContent)",
    "button.textContent='복사 완료 ✓'",
    "status.textContent='복사됨'",
    "status.textContent='선택한 내용을 직접 복사해 주세요.'",
    "setTimeout(()=>{button.textContent=originalLabel;if(status)status.textContent=''},2200)",
)


def contract_errors(root=ROOT):
    issues = []
    css = (root / "assets/site.css").read_text(encoding="utf-8")
    js = (root / "assets/site.js").read_text(encoding="utf-8")
    match = re.search(r":root\s*\{([^}]*)\}", css)
    variables = dict(re.findall(r"(--[a-z\d-]+)\s*:\s*([^;]+)", match.group(1))) if match else {}
    for name, value in TOKENS.items():
        if variables.get(name, "").strip() != value:
            issues.append(f"design token changed or missing: {name}")
    for snippet in CSS_CONTRACT:
        if snippet not in css:
            issues.append(f"shared CSS contract missing: {snippet}")
    for snippet in JS_CONTRACT:
        if snippet not in js:
            issues.append(f"copy behavior contract missing: {snippet}")
    if "복사했다." in js:
        issues.append("legacy copy feedback reintroduced")
    return issues


if __name__ == "__main__":
    errors = contract_errors()
    print("\n".join(errors) if errors else "PASS: shared design tokens and copy feedback contract")
    sys.exit(bool(errors))
