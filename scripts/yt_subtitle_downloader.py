#!/usr/bin/env python3
"""
YouTube 자막 일괄 다운로드 (URL 목록 파일용)
===========================================

URL이 담긴 텍스트 파일(또는 --url)로 여러 영상의 자막을 한 번에 받아
타임코드를 제거한 순수 텍스트(.txt)로 저장합니다.
채널/재생목록을 통째로 받거나 새 영상만 받고 싶다면 auto_subtitle_downloader.py를 쓰세요.

사전 준비:
  pip install yt-dlp --break-system-packages

사용법 (저장소 루트에서 실행):
  # URL 목록 파일 (한 줄에 하나, 앞에 제목이 붙어 있어도 URL만 추출)
  python scripts/yt_subtitle_downloader.py --file "authors/Joohan Kim/urls.txt" --outdir "authors/Joohan Kim/subtitles"

  # URL 직접 지정 (여러 번 가능)
  python scripts/yt_subtitle_downloader.py --url "https://youtu.be/xxxx" --url "https://youtu.be/yyyy"

  # 인자가 없으면 대화형으로 물어봅니다
  python scripts/yt_subtitle_downloader.py

옵션:
  --file       URL이 담긴 텍스트 파일
  --url        URL 하나 (여러 번 사용 가능)
  --outdir     저장 폴더 (기본값: ./subtitles)
  --lang       자막 언어 우선순위, 콤마 구분 (기본값: ko)
  --auto-only  자동생성 자막만 사용 (수동 자막 무시)

다운로드에 실패한 URL은 <outdir>/failed_urls.txt에 사유와 함께 기록됩니다.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from subtitle_utils import require_ytdlp, sanitize_name, vtt_to_plain_text

URL_RE = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w\-]+[^\s]*'
    r'|youtu\.be/[\w\-]+[^\s]*|youtube\.com/shorts/[\w\-]+[^\s]*)'
)


def extract_urls_from_text(text: str) -> list:
    """텍스트에서 YouTube URL만 순서를 유지하며 중복 없이 추출합니다."""
    return list(dict.fromkeys(URL_RE.findall(text)))


def read_urls_interactively() -> list:
    print("=" * 60)
    print("YouTube 자막 일괄 다운로드")
    print("=" * 60)
    print("  1) URL이 담긴 텍스트 파일 경로 입력")
    print("  2) URL을 여러 줄로 직접 붙여넣기 (빈 줄 입력 시 종료)")
    if input("선택 (1 또는 2): ").strip() == "1":
        path = Path(input("파일 경로를 입력하세요: ").strip().strip('"'))
        if not path.exists():
            sys.exit(f"오류: 파일을 찾을 수 없습니다 - {path}")
        return extract_urls_from_text(path.read_text(encoding="utf-8", errors="ignore"))

    print("URL을 한 줄씩 붙여넣으세요 (완료하려면 빈 줄에서 Enter):")
    lines = []
    while (line := input()).strip():
        lines.append(line)
    return extract_urls_from_text("\n".join(lines))


def download_subtitle(ytdlp: list, url: str, outdir: Path, langs: str, auto_only: bool):
    """영상 하나의 자막을 받아 저장합니다. (성공 여부, 저장 경로 또는 실패 사유)를 돌려줍니다."""
    work_dir = outdir / "_tmp_vtt"
    work_dir.mkdir(parents=True, exist_ok=True)

    cmd = ytdlp + [
        "--skip-download",
        "--sub-lang", langs,
        "--sub-format", "vtt",
        "--output", str(work_dir / "%(id)s.%(ext)s"),
        "--print", "before_dl:%(title)s",   # 제목도 같은 호출에서 함께 얻습니다
        "--no-warnings",
        *(["--write-auto-sub"] if auto_only else ["--write-sub", "--write-auto-sub"]),
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return False, "시간 초과"

    if result.returncode != 0:
        stderr = result.stderr.strip()
        return False, stderr.splitlines()[-1] if stderr else "알 수 없는 오류"

    vtt_files = sorted(work_dir.glob("*.vtt"))
    if not vtt_files:
        return False, "자막 없음"

    priority = [l.strip() for l in langs.split(",") if l.strip()]

    def rank(path: Path) -> int:
        for i, lang in enumerate(priority):
            if f".{lang}." in path.name:
                return i
        return len(priority)

    chosen = min(vtt_files, key=rank)
    title = sanitize_name(result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "untitled")

    out_path = outdir / f"{title}.txt"
    counter = 1
    while out_path.exists():
        out_path = outdir / f"{title}_{counter}.txt"
        counter += 1
    out_path.write_text(vtt_to_plain_text(chosen), encoding="utf-8")

    for vtt in vtt_files:
        vtt.unlink(missing_ok=True)
    return True, str(out_path)


def main():
    parser = argparse.ArgumentParser(description="YouTube 자막을 TXT로 일괄 다운로드합니다.")
    parser.add_argument("--file", help="URL이 담긴 텍스트 파일 경로")
    parser.add_argument("--url", action="append", default=[], help="YouTube URL (여러 번 사용 가능)")
    parser.add_argument("--outdir", default="./subtitles", help="저장 폴더 (기본값: ./subtitles)")
    parser.add_argument("--lang", default="ko", help="우선 자막 언어 코드, 콤마 구분 (기본값: ko)")
    parser.add_argument("--auto-only", action="store_true", help="자동생성 자막만 사용")
    args = parser.parse_args()

    ytdlp = require_ytdlp()

    urls = list(args.url)
    if args.file:
        path = Path(args.file)
        if not path.exists():
            sys.exit(f"오류: 파일을 찾을 수 없습니다 - {args.file}")
        urls += extract_urls_from_text(path.read_text(encoding="utf-8", errors="ignore"))
    if not urls:
        urls = read_urls_interactively()
    urls = list(dict.fromkeys(urls))
    if not urls:
        sys.exit("추출된 URL이 없습니다. 프로그램을 종료합니다.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"\n총 {len(urls)}개의 URL을 찾았습니다. 저장 폴더: {outdir.resolve()}\n")

    failed = []
    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] 처리 중: {url}")
        ok, info = download_subtitle(ytdlp, url, outdir, args.lang, args.auto_only)
        if ok:
            print(f"  ✓ 저장 완료: {Path(info).name}")
        else:
            print(f"  ✗ 실패: {info}")
            failed.append((url, info))

    shutil.rmtree(outdir / "_tmp_vtt", ignore_errors=True)

    print("\n" + "=" * 60)
    print(f"완료: 성공 {len(urls) - len(failed)}건 / 실패 {len(failed)}건")
    print("=" * 60)

    if failed:
        log = outdir / "failed_urls.txt"
        log.write_text("".join(f"{u}\t사유: {r}\n" for u, r in failed), encoding="utf-8")
        print(f"실패한 URL 목록은 다음 파일에 저장했습니다: {log}")


if __name__ == "__main__":
    main()
