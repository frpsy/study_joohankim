"""PR 본문의 변경 영향도 설명 유무를 검사한다. GitHub Actions에서 PR 이벤트에 적용."""
import os
import re
import sys

HEADINGS = ("변경 범위", "영향 기능", "검증 증거", "남은 위험")


def impact_errors(body: str):
    errors = []
    for heading in HEADINGS:
        match = re.search(r"(?m)^#{2,3}\s+" + re.escape(heading) + r"\s*$", body)
        if not match:
            errors.append(f"missing section: {heading}")
            continue
        remainder = body[match.end():]
        section = re.split(r"(?m)^#{2,3}\s+", remainder, maxsplit=1)[0]
        section = re.sub(r"<!--.*?-->", "", section, flags=re.S).strip()
        if len(section) < 12:
            errors.append(f"section needs meaningful explanation: {heading}")
    return errors


if __name__ == "__main__":
    errors = impact_errors(os.environ.get("PR_BODY", ""))
    print("\n".join(errors) if errors else "PASS: PR impact analysis has all four sections")
    sys.exit(bool(errors))
