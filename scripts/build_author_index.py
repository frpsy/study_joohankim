#!/usr/bin/env python3
"""authors/<이름>/db/lectures.json 으로부터 INDEX.md 를 생성한다.

사용: python3 scripts/build_author_index.py "authors/Jegal Geon"
"""
import json
import sys
from pathlib import Path


def build(author_dir: Path) -> Path:
    data = json.loads((author_dir / "db" / "lectures.json").read_text(encoding="utf-8"))
    items = data["items"]
    done = sum(i["status"] == "summarized" for i in items)
    lines = [
        f"# {data['author']} 강의 인덱스",
        "",
        data["description"],
        "",
        f"- 전체 {len(items)}편 / 요약 완료 {done}편",
        "- 원본 데이터: `db/lectures.json` (이 파일은 `scripts/build_author_index.py`로 생성)",
        "",
        "| 회차 | 제목 | 상태 | 키워드 |",
        "|---:|---|---|---|",
    ]
    for i in items:
        mark = "요약" if i["status"] == "summarized" else "-"
        lines.append(f"| {i['lecture_no']:03d} | [{i['title']}]({i['file'].split('authors/')[-1].split('/', 1)[1].replace(' ', '%20').replace('(', '%28').replace(')', '%29')}) | {mark} | {', '.join(i['keywords'])} |")
    lines += ["", "## 요약", ""]
    for i in items:
        if i["status"] != "summarized":
            continue
        lines += [f"### {i['lecture_no']:03d}. {i['title']}", ""]
        lines += [f"- {s}" for s in i["summary"]]
        if i["notes"]:
            lines += ["", f"> 비고: {i['notes']}"]
        lines.append("")
    out = author_dir / "INDEX.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build(Path(sys.argv[1])))
