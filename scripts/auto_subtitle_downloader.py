#!/usr/bin/env python3
"""
YouTube 자막 스마트 다운로드 (단일 영상/재생목록/채널 자동 판단)
=====================================================

URL 하나만 주면:
  1) 그게 단일 영상인지, 재생목록인지, 채널인지 자동으로 판단하고
  2) 저장소의 기존 폴더 구조(authors/<이름>/subtitles)를 고려해서
     저장 폴더를 알아서 만들거나, 원하면 직접 지정할 수 있고
  3) 자막을 받아서 파일 이름을 (재생목록/채널이면 순서 번호 + 다듬은 제목으로,
     단일 영상이면 다듬은 제목만으로) 구분하기 쉽게 정리해 저장합니다.

다른 스크립트를 import하지 않는 독립 실행 스크립트입니다.

사전 준비:
  pip install yt-dlp --break-system-packages

사용법:
  # 완전 대화형 (URL만 입력하면 나머지는 전부 자동/질문으로 진행)
  python scripts/auto_subtitle_downloader.py

  # URL을 바로 지정 (단일 영상/재생목록/채널 무엇이든 그대로 붙여넣으면 됨)
  python scripts/auto_subtitle_downloader.py --url "https://www.youtube.com/@어떤채널"

  # 저장 폴더를 직접 지정하고 싶을 때 (자동 판단 건너뜀)
  python scripts/auto_subtitle_downloader.py --url "..." --outdir authors/이름/subtitles

  # 빠른 테스트: 실제로 받지 않고 무엇을 어디에 어떻게 저장할지만 미리보기
  python scripts/auto_subtitle_downloader.py --url "..." --dry-run

  # 빠른 테스트: 앞의 3개 영상만 받아보기
  python scripts/auto_subtitle_downloader.py --url "..." --limit 3

옵션:
  --url                    단일 영상 / 재생목록 / 채널 URL (무엇이든 자동 판단)
  --outdir                 저장 폴더 경로. 지정하지 않으면 저장소의 authors/ 구조를
                           고려해 자동 생성하며, 실행 중 원하는 이름으로 바꿀지 물어봅니다.
  --limit                  앞에서부터 N개 영상만 처리 (빠른 테스트용)
  --dry-run                실제로 다운로드하지 않고, 판단 결과/저장 위치/파일명 계획만 출력
  --lang                   우선 자막 언어 코드, 콤마 구분 가능 (기본값: ko,en)
                           우선순위대로 하나씩만 요청하며, 먼저 찾은 언어만 사용합니다.
                           단, 영상의 자동자막 원본 언어를 판별할 수 있으면 그 언어를
                           이 목록보다 항상 먼저 시도합니다 (번역된 자막 대신 원본 우선).
  --auto-only              자동생성 자막만 사용 (수동 자막 무시)
  --sleep                  영상 처리 사이 최소 대기 시간(초) (기본값: 5, 429 발생 시 자동으로 늘어남)
  --retries                429 오류 시 영상당 재시도 횟수 (기본값: 3)
  --cookies                쿠키 파일 경로 (Netscape 형식). 429가 계속되면 사용하세요.
  --cookies-from-browser   설치된 브라우저에서 쿠키를 가져옵니다 (예: chrome, firefox, edge)

참고 (429/Too Many Requests가 계속될 때):
  유튜브가 자막 요청을 IP 단위로 차단한 것이므로 코드 문제가 아닙니다.
  1) 잠시(수십 분) 쉬었다가 다시 시도하거나
  2) --cookies-from-browser chrome 등으로 로그인 쿠키를 사용하면 훨씬 덜 차단됩니다.
  중단됐다 다시 실행해도 이미 받은 영상은 건너뛰고 이어받습니다.
"""

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# yt-dlp 실행 방식
# ---------------------------------------------------------------------------

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


def cookie_cli_args(cookies: str = None, cookies_from_browser: str = None) -> list:
    if cookies:
        return ["--cookies", cookies]
    if cookies_from_browser:
        return ["--cookies-from-browser", cookies_from_browser]
    return []


def sanitize_name(name: str) -> str:
    """파일/폴더명으로 쓸 수 없는 문자를 제거/치환합니다."""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.strip().strip(".")
    return name[:150] or "untitled"


def clean_title(title: str) -> str:
    """제목 앞뒤 공백/구분기호를 정리해서 파일명으로 쓰기 좋게 다듬습니다."""
    if not title:
        return "untitled"
    t = re.sub(r'\s+', ' ', title).strip()
    t = t.strip(' -_·')
    return sanitize_name(t or "untitled")


# ---------------------------------------------------------------------------
# 1단계: URL 판별(단일 영상/재생목록/채널) + URL 추출 + 제목/업로더 조회
# ---------------------------------------------------------------------------

def detect_source_type(url: str, result: dict) -> str:
    """URL과 추출 결과를 바탕으로 '영상' / '재생목록' / '채널'을 판단합니다."""
    if 'entries' not in result and result.get('_type') not in ('playlist', 'multi_video'):
        return 'video'
    if re.search(r'/(channel/|@|c/|user/)', url):
        return 'channel'
    if 'list=' in url:
        return 'playlist'
    return 'playlist'


SOURCE_TYPE_LABEL = {
    'video': '단일 영상',
    'playlist': '재생목록',
    'channel': '채널',
}


def extract_source(source: str, cookies: str = None, cookies_from_browser: str = None):
    """URL에서 (종류, 제목, 업로더, 채널ID, 영상 URL 목록)을 추출합니다."""
    import yt_dlp

    url = source
    if 'list=' in url and 'playlist?list=' not in url:
        playlist_id = re.search(r'list=([^&]+)', url)
        if playlist_id:
            url = f"https://www.youtube.com/playlist?list={playlist_id.group(1)}"
    elif re.search(r'/(channel/|@|c/|user/)', url) and not re.search(
            r'/(videos|shorts|streams|playlists|featured)/?(\?|$)', url):
        # 채널 주소를 탭 지정 없이 그대로 주면 영상/쇼츠/라이브/재생목록 탭이 중첩된 구조로
        # 나와서 실제 영상 목록을 못 찾는 경우가 있습니다. "영상" 탭을 명시해 평탄한 목록으로 받습니다.
        url = url.rstrip('/') + '/videos'

    ydl_opts = {
        'extract_flat': True,
        'ignoreerrors': True,
        'noplaylist': False,
    }
    if cookies:
        ydl_opts['cookiefile'] = cookies
    elif cookies_from_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)

    print(f"\n[안내] 주소를 분석 중입니다: {url}")
    print("[안내] 영상이 많을 경우 시간이 다소 소요될 수 있습니다...\n")

    video_urls = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)

        if not result:
            return None, None, None, None, video_urls

        source_type = detect_source_type(url, result)
        title = result.get('title')
        uploader = result.get('uploader') or result.get('channel') or title
        channel_id = result.get('channel_id') or result.get('uploader_id') or ""

        if 'entries' in result:
            entries = result['entries']
        elif result.get('_type') == 'playlist':
            entries = result.get('entries', [])
        else:
            entries = [result]

        for entry in entries:
            if not entry:
                continue
            if entry.get('_type') in ('playlist', 'multi_video'):
                continue

            video_id = entry.get('id') or entry.get('url')
            if not video_id:
                continue

            if str(video_id).startswith('http'):
                video_url = video_id
            else:
                # 채널의 "재생목록" 탭 등은 _type이 'url'로 나와 위 필터를 통과하지만
                # id가 영상이 아니라 재생목록 ID(11자가 아님)이므로 여기서 걸러냅니다.
                if not re.fullmatch(r'[\w-]{11}', str(video_id)):
                    continue
                video_url = f"https://www.youtube.com/watch?v={video_id}"

            if video_url not in video_urls:
                video_urls.append(video_url)

    return source_type, title, uploader, channel_id, video_urls


def step1_extract(source: str, cookies: str = None, cookies_from_browser: str = None):
    print("=" * 60)
    print("1단계: 주소 판별 + 영상 목록 추출")
    print("=" * 60)

    try:
        source_type, title, uploader, channel_id, video_urls = extract_source(
            source, cookies=cookies, cookies_from_browser=cookies_from_browser
        )
    except Exception as e:
        print(f"[오류] 데이터 추출 중 문제가 발생했습니다: {e}")
        sys.exit(1)

    if not video_urls:
        print("[오류] URL 추출에 실패했습니다. 주소를 확인해주세요.")
        sys.exit(1)

    label = SOURCE_TYPE_LABEL.get(source_type, '알 수 없음')
    print("-" * 50)
    print(f"★ 판별 결과: {label} (제목: {title or '알 수 없음'} / 업로더: {uploader or '알 수 없음'})")
    print(f"★ 총 {len(video_urls)}개의 영상 URL을 찾았습니다.")
    print("-" * 50)

    return source_type, title, uploader, channel_id, video_urls


# ---------------------------------------------------------------------------
# 저장 폴더 결정 (저장소의 authors/<이름>/subtitles 구조를 고려해 자동 생성)
# ---------------------------------------------------------------------------

CHANNEL_ID_MARKER = ".channel_id"


def find_repo_authors_dir() -> Path:
    """이 스크립트가 속한 저장소에 authors/ 폴더가 있으면 그 경로를 돌려줍니다."""
    repo_root = Path(__file__).resolve().parent.parent
    authors_dir = repo_root / "authors"
    if authors_dir.is_dir():
        return authors_dir
    return None


def find_matching_author_folder(authors_dir: Path, channel_id: str, *text_candidates: str):
    """authors/ 밑에서 이 채널에 해당하는 기존 폴더를 찾습니다.

    1) 채널ID로 정확히 매칭 (한 번이라도 매칭된 폴더는 .channel_id에 기록해두므로,
       다음부터는 제목에 한글 이름이 없는 단일 영상이어도 정확히 찾을 수 있습니다).
    2) 채널ID로 못 찾으면, 제목/업로더 문자열 안에 기존 폴더 이름이 들어있는지로 보조 매칭합니다.
       (유튜브 메타데이터의 uploader/channel은 보통 영문 채널명이라 예: "Joohan Kim's ...",
       저장소가 이미 쓰는 한글 이름 "김주환"과 다를 때가 많은데, 재생목록/영상 제목에는
       한글 이름이 그대로 들어있는 경우가 많기 때문입니다.)
    """
    if authors_dir is None:
        return None
    existing = [d for d in authors_dir.iterdir() if d.is_dir()]

    if channel_id:
        for d in existing:
            marker = d / CHANNEL_ID_MARKER
            if marker.exists() and marker.read_text(encoding="utf-8").strip() == channel_id:
                return d

    for cand in text_candidates:
        if not cand:
            continue
        for d in existing:
            if d.name and d.name in cand:
                return d

    return None


def remember_channel_id(author_dir: Path, channel_id: str):
    """다음부터 채널ID만으로 이 폴더를 바로 찾을 수 있도록 기록해둡니다."""
    if not channel_id:
        return
    marker = author_dir / CHANNEL_ID_MARKER
    if not marker.exists():
        author_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text(channel_id, encoding="utf-8")


def auto_outdir(uploader: str, title: str, channel_id: str = "") -> Path:
    authors_dir = find_repo_authors_dir()

    matched = find_matching_author_folder(authors_dir, channel_id, title, uploader)
    if matched is not None:
        return matched / "subtitles"

    channel_name = sanitize_name(uploader or title or "youtube")
    if authors_dir is not None:
        return authors_dir / channel_name / "subtitles"
    return Path.cwd() / channel_name


def resolve_outdir(args, uploader: str, title: str, channel_id: str = "") -> Path:
    if args.outdir:
        return Path(args.outdir)

    auto_path = auto_outdir(uploader, title, channel_id)

    try:
        user_input = input(
            f"저장 폴더를 입력하세요 (엔터 시 자동 생성: '{auto_path}'): "
        ).strip().strip('"').strip("'")
    except EOFError:
        user_input = ""

    if not user_input:
        print(f"[안내] 입력값이 없어 자동 생성 폴더 '{auto_path}'를 사용합니다.")
        return auto_path

    return Path(user_input)


def prompt_for_url(args):
    if not args.url:
        try:
            args.url = input("단일 영상 / 재생목록 / 채널 URL을 입력하세요: ").strip().strip('"').strip("'")
        except EOFError:
            args.url = ""
        if not args.url:
            print("[종료] 입력된 URL이 없어 프로그램을 종료합니다.")
            sys.exit(1)


# ---------------------------------------------------------------------------
# 2단계: 자막 다운로드
# ---------------------------------------------------------------------------

def vtt_to_plain_text(vtt_path: Path) -> str:
    """VTT 자막 파일을 읽어 타임코드/태그를 제거한 순수 텍스트로 변환합니다."""
    with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    text_lines = []
    seen_lines = set()

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
        if re.match(r'^\d+$', line):
            continue
        line = re.sub(r'<[^>]+>', '', line)
        line = line.strip()
        if not line:
            continue
        if line in seen_lines:
            continue
        seen_lines.add(line)
        text_lines.append(line)

    return "\n".join(text_lines)


def is_rate_limited(stderr_text: str) -> bool:
    if not stderr_text:
        return False
    lowered = stderr_text.lower()
    return "429" in lowered or "too many requests" in lowered


def extract_video_id(url: str) -> str:
    match = re.search(r'(?:v=|youtu\.be/|shorts/)([\w-]{6,})', url)
    return match.group(1) if match else url


def load_done_ids(outdir: Path) -> set:
    """이전 실행에서 이미 성공한 영상 ID 목록을 읽어옵니다 (429로 중단됐다 재실행할 때 이어받기용)."""
    manifest = outdir / ".downloaded_ids.txt"
    if not manifest.exists():
        return set()
    return set(manifest.read_text(encoding="utf-8").splitlines())


def mark_done(outdir: Path, video_id: str):
    manifest = outdir / ".downloaded_ids.txt"
    with open(manifest, "a", encoding="utf-8") as f:
        f.write(video_id + "\n")


def detect_original_lang(url: str, cookies: str = None, cookies_from_browser: str = None) -> str:
    """영상의 자동 자막 중 번역되지 않은 원본 언어를 판별합니다.

    유튜브 자동생성 자막은 실제 발화 언어(원본) 하나만 진짜로 생성되고, 나머지 언어는
    그걸 구글 번역으로 옮긴 것들입니다. 번역된 트랙은 자막 URL에 'tlang=' 파라미터가
    붙어있고, 원본 트랙만 그게 없어서 이걸로 구분할 수 있습니다.
    """
    import yt_dlp

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    if cookies:
        ydl_opts['cookiefile'] = cookies
    elif cookies_from_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return None

    if not info:
        return None

    for lang, fmts in (info.get('automatic_captions') or {}).items():
        for fmt in fmts:
            if 'tlang=' not in (fmt.get('url') or ''):
                return lang

    return None


def _try_single_lang(url: str, work_dir: Path, out_template: str, lang: str, auto_only: bool,
                      cookies: str, cookies_from_browser: str, retries: int):
    """언어 하나에 대해서만 자막 다운로드를 시도합니다 (429 시 재시도 포함).

    반환값: (성공 여부, 제목 또는 None, 429 여부, 마지막 대기시간(초), 에러 메시지 또는 None)
    """
    ytdlp_cmd = get_ytdlp_cmd()
    cmd = ytdlp_cmd + [
        "--skip-download",
        "--sub-lang", lang,
        "--sub-format", "vtt",
        "--output", out_template,
        # 제목도 같은 호출에서 함께 얻어 영상당 요청 횟수를 줄입니다.
        "--print", "before_dl:%(title)s",
        "--no-warnings",
    ]
    cmd += cookie_cli_args(cookies, cookies_from_browser)
    if auto_only:
        cmd.append("--write-auto-sub")
    else:
        cmd += ["--write-sub", "--write-auto-sub"]
    cmd.append(url)

    attempt = 0
    wait = 0
    while True:
        attempt += 1
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return False, None, False, wait, "시간 초과"

        if result.returncode == 0:
            return True, result.stdout.strip() or "untitled", False, wait, None

        if is_rate_limited(result.stderr) and attempt <= retries:
            wait = 20 * attempt
            print(f"  [경고] 429 감지({lang}), {wait}초 대기 후 재시도 {attempt}/{retries}...")
            time.sleep(wait)
            continue

        err_msg = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "알 수 없는 오류"
        return False, None, is_rate_limited(result.stderr), wait, err_msg


def build_filename_stem(index: int, total: int, source_type: str, title: str) -> str:
    """재생목록/채널이면 순서 번호를 붙이고, 단일 영상이면 제목만 사용합니다."""
    clean = clean_title(title)
    if source_type == 'video' or total <= 1:
        return clean
    pad = len(str(total))
    return f"{index:0{pad}d}_{clean}"


def download_batch(urls: list, outdir: Path, source_type: str, langs: str, auto_only: bool,
                    sleep: float = 5, retries: int = 3,
                    cookies: str = None, cookies_from_browser: str = None,
                    max_rate_limit_cooldowns: int = 3):
    success_list = []
    fail_list = []
    consecutive_rate_limits = 0
    cooldowns_used = 0

    # 영상 사이 대기 시간을 429 발생 여부에 맞춰 스스로 조절합니다.
    dynamic_sleep = sleep
    clean_streak = 0

    # 이전 실행에서 이미 받아둔 영상은 건너뜁니다 (429로 중단됐다가 다시 실행하는 경우 대비).
    done_ids = load_done_ids(outdir)
    total = len(urls)

    for i, url in enumerate(urls, start=1):
        video_id = extract_video_id(url)
        if video_id in done_ids:
            print(f"\n[{i}/{total}] 이미 받은 영상이라 건너뜁니다: {url}")
            success_list.append((url, "이전 실행에서 이미 다운로드됨"))
            continue

        ok, u, info, was_rate_limited, last_wait = download_subtitle(
            url, outdir, i, total, source_type, langs, auto_only, retries=retries,
            cookies=cookies, cookies_from_browser=cookies_from_browser,
        )

        if ok:
            success_list.append((u, info))
            consecutive_rate_limits = 0
            mark_done(outdir, video_id)
        else:
            fail_list.append((u, info))
            if was_rate_limited:
                consecutive_rate_limits += 1
            else:
                consecutive_rate_limits = 0

        if last_wait > 0:
            clean_streak = 0
            new_sleep = min(max(dynamic_sleep, last_wait), 150)
            if new_sleep > dynamic_sleep:
                print(f"  [자동조절] 429가 감지되어 영상 간 대기 시간을 {dynamic_sleep:.0f}초 → {new_sleep:.0f}초로 늘립니다.")
            dynamic_sleep = new_sleep
        else:
            clean_streak += 1
            if clean_streak >= 3 and dynamic_sleep > sleep:
                new_sleep = max(sleep, dynamic_sleep * 0.7)
                if new_sleep < dynamic_sleep:
                    print(f"  [자동조절] 최근 {clean_streak}개 연속 성공, 대기 시간을 {dynamic_sleep:.0f}초 → {new_sleep:.0f}초로 줄입니다.")
                dynamic_sleep = new_sleep
                clean_streak = 0

        if consecutive_rate_limits >= 1:
            cooldowns_used += 1
            if cooldowns_used > max_rate_limit_cooldowns:
                remaining = urls[i:]
                print(f"\n[중단] 429 오류가 {max_rate_limit_cooldowns}회 대기 후에도 반복되어, "
                      "유튜브가 현재 IP를 차단한 것으로 보입니다.")
                print(f"[중단] 남은 {len(remaining)}개 영상은 건너뜁니다. "
                      "잠시(수십 분) 기다리거나 --cookies / --cookies-from-browser로 로그인 쿠키를 사용해보세요.")
                for skipped_url in remaining:
                    fail_list.append((skipped_url, "반복된 429로 나머지 영상 처리를 중단함"))
                break

            print(f"\n[경고] 429 오류가 발생했습니다. 3분간 대기 후 계속 진행합니다... "
                  f"({cooldowns_used}/{max_rate_limit_cooldowns})")
            time.sleep(180)
            consecutive_rate_limits = 0

        if i < total and dynamic_sleep > 0:
            time.sleep(dynamic_sleep)

    return success_list, fail_list


def download_subtitle(url, outdir, index, total, source_type, langs, auto_only,
                       retries=3, cookies=None, cookies_from_browser=None):
    """영상 하나의 자막을 받아, 실제로 받아온 제목으로 순번+제목 파일명을 만들어 저장합니다.

    언어를 우선순위대로 하나씩만 요청합니다 (예: ko 시도 → 있으면 바로 종료, 없을 때만 en 시도).
    한 번에 "ko,en"을 같이 요청하면 yt-dlp가 존재하는 언어를 전부 실제로 받아버려서
    필요 없는 언어 요청까지 나가 429가 훨씬 잦아지기 때문입니다.

    단, 영상의 실제(원본) 언어를 판별할 수 있으면 그 언어를 이 우선순위 목록의
    맨 앞에 끼워 넣어 가장 먼저 시도합니다. 예를 들어 영상이 영어로 말하는 영상이면
    --lang이 "ko,en"이어도 번역된 한국어 자막 대신 원본 영어 자막을 먼저 받습니다.
    """
    work_dir = outdir / "_tmp_vtt"
    work_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(work_dir / "%(id)s.%(ext)s")

    print(f"\n[{index}/{total}] 처리 중: {url}")

    lang_priority = [l.strip() for l in langs.split(",") if l.strip()]

    original_lang = detect_original_lang(url, cookies, cookies_from_browser)
    if original_lang:
        if original_lang in lang_priority:
            lang_priority.remove(original_lang)
        lang_priority.insert(0, original_lang)

    last_wait = 0
    last_err = "자막 없음"
    was_rate_limited = False
    vtt_files = []
    title = "untitled"

    for lang in lang_priority:
        ok, lang_title, rl, wait, msg = _try_single_lang(
            url, work_dir, out_template, lang, auto_only, cookies, cookies_from_browser, retries
        )
        last_wait = max(last_wait, wait)

        if not ok:
            was_rate_limited = rl
            last_err = msg or last_err
            if rl:
                break
            continue

        title = lang_title
        vtt_files = sorted(work_dir.glob("*.vtt"))
        if vtt_files:
            was_rate_limited = False
            break

    if not vtt_files:
        if was_rate_limited:
            print(f"  ✗ 실패: {last_err}")
        else:
            print(f"  ✗ 자막 파일을 찾지 못했습니다 (자막이 없는 영상일 수 있습니다): {url}")
        return False, url, last_err, was_rate_limited, last_wait

    chosen = vtt_files[0]
    plain_text = vtt_to_plain_text(chosen)

    filename_stem = build_filename_stem(index, total, source_type, title)
    out_path = outdir / f"{filename_stem}.txt"
    counter = 1
    while out_path.exists():
        out_path = outdir / f"{filename_stem}_{counter}.txt"
        counter += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(plain_text)

    for vf in vtt_files:
        try:
            vf.unlink()
        except OSError:
            pass

    print(f"  ✓ 저장 완료: {out_path.name}")
    return True, url, str(out_path), False, last_wait


def write_fail_log(outdir: Path, fail_list: list):
    if not fail_list:
        return None
    fail_log_path = outdir / "failed_urls.txt"
    with open(fail_log_path, "w", encoding="utf-8") as f:
        for u, reason in fail_list:
            f.write(f"{u}\t사유: {reason}\n")
    return fail_log_path


def step2_download_subtitles(urls: list, outdir: Path, source_type: str, lang: str, auto_only: bool,
                              sleep: float = 5, retries: int = 3,
                              cookies: str = None, cookies_from_browser: str = None):
    print("\n" + "=" * 60)
    print("2단계: 자막 다운로드")
    print("=" * 60)
    print(f"총 {len(urls)}개의 URL을 처리합니다. 저장 폴더: {outdir.resolve()}\n")

    success_list, fail_list = download_batch(urls, outdir, source_type, lang, auto_only,
                                              sleep=sleep, retries=retries,
                                              cookies=cookies, cookies_from_browser=cookies_from_browser)

    tmp_dir = outdir / "_tmp_vtt"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n다운로드 완료: 성공 {len(success_list)}건 / 실패 {len(fail_list)}건")

    fail_log_path = write_fail_log(outdir, fail_list)
    if fail_log_path:
        print(f"실패한 URL 목록은 다음 파일에 저장했습니다: {fail_log_path}")

    return success_list, fail_list


def main():
    parser = argparse.ArgumentParser(
        description="단일 영상/재생목록/채널을 자동으로 판단해 자막을 다운로드하고, "
                    "저장소 구조(authors/이름/subtitles)를 고려해 폴더를 자동 생성합니다."
    )
    parser.add_argument("--url", help="단일 영상 / 재생목록 / 채널 URL")
    parser.add_argument("--outdir", help="저장 폴더 경로 (지정하지 않으면 자동 생성 여부를 물어봅니다)")
    parser.add_argument("--limit", type=int, help="앞에서부터 N개 영상만 처리 (빠른 테스트용)")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제로 다운로드하지 않고 판단 결과/저장 위치/파일명 계획만 출력")
    parser.add_argument("--lang", default="ko,en", help="우선 자막 언어 코드, 콤마 구분 가능 (기본값: ko,en)")
    parser.add_argument("--auto-only", action="store_true", help="자동생성 자막만 사용")
    parser.add_argument("--sleep", type=float, default=5, help="영상 처리 사이 최소 대기 시간(초) (기본값: 5)")
    parser.add_argument("--retries", type=int, default=3, help="429 오류 시 영상당 재시도 횟수 (기본값: 3)")
    parser.add_argument("--cookies", help="쿠키 파일 경로 (Netscape 형식). 429가 계속되면 사용하세요.")
    parser.add_argument("--cookies-from-browser", metavar="BROWSER",
                        help="설치된 브라우저에서 쿠키를 가져옵니다 (예: chrome, firefox, edge)")
    args = parser.parse_args()

    if check_ytdlp_installed() is None:
        print("오류: yt-dlp가 설치되어 있지 않습니다.")
        print("다음 명령으로 먼저 설치해 주세요: pip install yt-dlp --break-system-packages")
        sys.exit(1)

    prompt_for_url(args)

    source_type, title, uploader, channel_id, video_urls = step1_extract(
        args.url, cookies=args.cookies, cookies_from_browser=args.cookies_from_browser
    )

    if args.limit and args.limit > 0:
        video_urls = video_urls[:args.limit]
        print(f"[안내] --limit {args.limit} 지정으로 앞의 {len(video_urls)}개 영상만 처리합니다.")

    outdir = resolve_outdir(args, uploader, title, channel_id)

    authors_dir = find_repo_authors_dir()
    resolved_outdir = outdir.resolve()
    if (authors_dir is not None and resolved_outdir.name == "subtitles"
            and resolved_outdir.parent.parent == authors_dir.resolve()):
        remember_channel_id(resolved_outdir.parent, channel_id)

    if args.dry_run:
        print("\n" + "=" * 60)
        print("[dry-run] 실제로 다운로드하지 않고 계획만 보여줍니다.")
        print("=" * 60)
        print(f"저장 폴더: {outdir.resolve()}")
        total = len(video_urls)
        if total > 1:
            print("(실제 파일명의 제목 부분은 다운로드 시점에 각 영상의 진짜 제목으로 채워집니다)")
        for i, u in enumerate(video_urls, start=1):
            stem = build_filename_stem(i, total, source_type, "영상 제목")
            print(f"  [{i}/{total}] {u}  ->  {stem}.txt")
        print("\n(--dry-run 이므로 실제 파일은 만들지 않았습니다.)")
        return

    outdir.mkdir(parents=True, exist_ok=True)

    with open(outdir / "urls.txt", "w", encoding="utf-8") as f:
        for u in video_urls:
            f.write(u + "\n")

    step2_download_subtitles(video_urls, outdir, source_type, args.lang, args.auto_only,
                              sleep=args.sleep, retries=args.retries,
                              cookies=args.cookies, cookies_from_browser=args.cookies_from_browser)

    print("\n" + "=" * 60)
    print(f"전체 완료! 저장 폴더: {outdir.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
