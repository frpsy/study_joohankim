#!/usr/bin/env python3
"""
YouTube 자막 일괄 다운로드 프로그램
=====================================

기능:
  - YouTube URL을 직접 붙여넣거나, URL이 담긴 텍스트 파일을 입력해서
    각 영상의 자막을 TXT 파일로 일괄 다운로드합니다.
  - 한국어 자막(수동 자막)을 우선 사용하고, 없으면 자동생성 자막을 사용합니다.
  - 타임코드/스타일 태그를 제거한 순수 텍스트만 저장합니다.

사전 준비:
  pip install yt-dlp --break-system-packages
  (yt-dlp는 시스템에 실제로 설치된 ffmpeg 없이도 자막만 받는 데는 문제 없습니다)

사용법 (저장소 루트에서 실행):
  1) 대화형 실행
     python scripts/yt_subtitle_downloader.py

  2) URL을 담은 텍스트 파일로 실행 (한 줄에 하나씩, 제목과 URL이 같이 있어도 됨)
     python scripts/yt_subtitle_downloader.py --file authors/김주환/urls.txt --outdir authors/김주환/subtitles

  3) 커맨드라인에 URL 직접 나열
     python scripts/yt_subtitle_downloader.py --url "https://www.youtube.com/watch?v=xxxx" --url "https://youtu.be/yyyy"

  4) 새로운 저자/교수님 강의를 추가할 때
     mkdir -p authors/<이름>/subtitles
     python scripts/yt_subtitle_downloader.py --file authors/<이름>/urls.txt --outdir authors/<이름>/subtitles

옵션:
  --file      URL이 담긴 텍스트 파일 경로 (한 줄에 URL 하나, 앞에 제목이 있어도 자동으로 URL만 추출)
  --url       URL 하나 (여러 번 사용 가능)
  --outdir    저장 폴더 (기본값: ./subtitles)
  --lang      우선 자막 언어 코드 (기본값: ko). 콤마로 여러 개 지정 가능 (예: ko,en)
  --auto-only 자동생성 자막만 사용 (수동 자막 무시)
"""

import argparse
import os
import re
import sys
import subprocess
import shutil
from pathlib import Path


def extract_urls_from_text(text: str):
    """텍스트(파일 내용 또는 붙여넣은 텍스트)에서 YouTube URL만 추출합니다."""
    pattern = r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w\-]+[^\s]*|youtu\.be/[\w\-]+[^\s]*|youtube\.com/shorts/[\w\-]+[^\s]*))'
    urls = re.findall(pattern, text)
    # 중복 제거 (순서 유지)
    seen = set()
    result = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result


def sanitize_filename(name: str) -> str:
    """파일명으로 쓸 수 없는 문자를 제거/치환합니다."""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.strip()
    return name[:150]  # 너무 긴 파일명 방지


def vtt_to_plain_text(vtt_path: Path) -> str:
    """VTT 자막 파일을 읽어 타임코드/태그를 제거한 순수 텍스트로 변환합니다."""
    with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    text_lines = []
    seen_lines = set()  # 자동생성 자막은 같은 줄이 여러 번 겹쳐 나오는 경우가 많아 중복 제거

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.upper().startswith("WEBVTT"):
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if re.match(r'^\d+$', line):  # 자막 번호(SRT 스타일)만 있는 줄
            continue
        # 인라인 타임태그 및 스타일 태그 제거 (예: <00:00:01.000><c> 단어</c>)
        line = re.sub(r'<[^>]+>', '', line)
        line = line.strip()
        if not line:
            continue
        if line in seen_lines:
            continue
        seen_lines.add(line)
        text_lines.append(line)

    return "\n".join(text_lines)


def get_ytdlp_cmd():
    """실행 가능한 yt-dlp 호출 방식을 찾습니다. CLI가 없으면 'python -m yt_dlp'를 사용합니다."""
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        return None


def check_ytdlp_installed():
    return get_ytdlp_cmd() is not None


def download_subtitle(url: str, outdir: Path, langs: str, auto_only: bool, index: int, total: int):
    print(f"\n[{index}/{total}] 처리 중: {url}")

    work_dir = outdir / "_tmp_vtt"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 임시 출력 템플릿 (영상 ID 기반, 이후 제목으로 리네임)
    out_template = str(work_dir / "%(id)s.%(ext)s")

    ytdlp_cmd = get_ytdlp_cmd()
    cmd = ytdlp_cmd + [
        "--skip-download",
        "--sub-lang", langs,
        "--sub-format", "vtt",
        "--output", out_template,
        "--no-warnings",
    ]
    if auto_only:
        cmd.append("--write-auto-sub")
    else:
        cmd += ["--write-sub", "--write-auto-sub"]  # 수동 자막 우선, 없으면 자동생성

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print(f"  ✗ 시간 초과: {url}")
        return False, url, "시간 초과"

    if result.returncode != 0:
        err_msg = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "알 수 없는 오류"
        print(f"  ✗ 실패: {err_msg}")
        return False, url, err_msg

    # 영상 제목 가져오기
    title_cmd = ytdlp_cmd + ["--skip-download", "--print", "%(title)s", "--no-warnings", url]
    try:
        title_result = subprocess.run(title_cmd, capture_output=True, text=True, timeout=60)
        title = title_result.stdout.strip() if title_result.returncode == 0 else "untitled"
    except subprocess.TimeoutExpired:
        title = "untitled"

    safe_title = sanitize_filename(title) if title else "untitled"

    # 다운로드된 vtt 파일 찾기 (언어 우선순위대로)
    vtt_files = sorted(work_dir.glob("*.vtt"))
    if not vtt_files:
        print(f"  ✗ 자막 파일을 찾지 못했습니다 (자막이 없는 영상일 수 있습니다): {url}")
        return False, url, "자막 없음"

    lang_priority = [l.strip() for l in langs.split(",")]

    def rank(path: Path):
        name = path.name
        for i, lang in enumerate(lang_priority):
            if f".{lang}." in name:
                return i
        return len(lang_priority)

    vtt_files.sort(key=rank)
    chosen = vtt_files[0]

    plain_text = vtt_to_plain_text(chosen)

    out_path = outdir / f"{safe_title}.txt"
    counter = 1
    while out_path.exists():
        out_path = outdir / f"{safe_title}_{counter}.txt"
        counter += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(plain_text)

    # 임시 vtt 파일 정리
    for vf in vtt_files:
        try:
            vf.unlink()
        except OSError:
            pass

    print(f"  ✓ 저장 완료: {out_path.name}")
    return True, url, str(out_path)


def main():
    parser = argparse.ArgumentParser(description="YouTube 자막을 TXT로 일괄 다운로드합니다.")
    parser.add_argument("--file", help="URL이 담긴 텍스트 파일 경로")
    parser.add_argument("--url", action="append", help="YouTube URL (여러 번 사용 가능)")
    parser.add_argument("--outdir", default="./subtitles", help="저장 폴더 (기본값: ./subtitles)")
    parser.add_argument("--lang", default="ko", help="우선 자막 언어 코드, 콤마 구분 가능 (기본값: ko)")
    parser.add_argument("--auto-only", action="store_true", help="자동생성 자막만 사용")
    args = parser.parse_args()

    if check_ytdlp_installed() is None:
        print("오류: yt-dlp가 설치되어 있지 않습니다.")
        print("다음 명령으로 먼저 설치해 주세요: pip install yt-dlp")
        sys.exit(1)

    # 기본 URL 파일을 youtube_urls.txt로 설정
    url_file = 'youtube_urls.txt'
    
    # URL 파일이 존재하는지 확인
    if not os.path.isfile(url_file):
        print(f"URL 파일 '{url_file}'이(가) 존재하지 않습니다.")
        sys.exit(1)
    
    # URL 파일에서 URL 읽기
    with open(url_file, 'r') as f:
        urls = f.read().splitlines()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"오류: 파일을 찾을 수 없습니다 - {args.file}")
            sys.exit(1)
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        urls = extract_urls_from_text(text)

    if args.url:
        urls.extend(args.url)

    # 대화형 모드: 인자가 아무것도 없으면 사용자 입력을 받음
    if not urls:
        print("=" * 60)
        print("YouTube 자막 일괄 다운로드")
        print("=" * 60)
        print("아래 중 하나를 선택해 주세요:")
        print("  1) URL이 담긴 텍스트 파일 경로 입력")
        print("  2) URL을 여러 줄로 직접 붙여넣기 (빈 줄 입력 시 종료)")
        choice = input("선택 (1 또는 2): ").strip()

        if choice == "1":
            file_path = input("파일 경로를 입력하세요: ").strip().strip('"')
            fp = Path(file_path)
            if not fp.exists():
                print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
                sys.exit(1)
            text = fp.read_text(encoding="utf-8", errors="ignore")
            urls = extract_urls_from_text(text)
        else:
            print("URL을 한 줄씩 붙여넣으세요 (완료하려면 빈 줄에서 Enter):")
            pasted_lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                pasted_lines.append(line)
            urls = extract_urls_from_text("\n".join(pasted_lines))

    if not urls:
        print("추출된 URL이 없습니다. 프로그램을 종료합니다.")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n총 {len(urls)}개의 URL을 찾았습니다. 저장 폴더: {outdir.resolve()}\n")

    success_list = []
    fail_list = []

    for i, url in enumerate(urls, start=1):
        ok, u, info = download_subtitle(url, outdir, args.lang, args.auto_only, i, len(urls))
        if ok:
            success_list.append((u, info))
        else:
            fail_list.append((u, info))

    # 임시 폴더 정리
    tmp_dir = outdir / "_tmp_vtt"
    if tmp_dir.exists():
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass

    print("\n" + "=" * 60)
    print(f"완료: 성공 {len(success_list)}건 / 실패 {len(fail_list)}건")
    print("=" * 60)

    if fail_list:
        fail_log_path = outdir / "failed_urls.txt"
        with open(fail_log_path, "w", encoding="utf-8") as f:
            for u, reason in fail_list:
                f.write(f"{u}\t사유: {reason}\n")
        print(f"실패한 URL 목록은 다음 파일에 저장했습니다: {fail_log_path}")


if __name__ == "__main__":
    main()