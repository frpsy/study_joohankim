#!/usr/bin/env python3
"""
YouTube 자막 도구 (스크립트 하나로 전부)
=========================================

  python scripts/subtitles.py <URL>                 자막 다운로드 (영상 / 재생목록 / 채널 자동 판별)
  python scripts/subtitles.py --file urls.txt       URL 목록 파일로 일괄 다운로드
  python scripts/subtitles.py <URL> --urls-only f   자막은 받지 않고 영상 URL 목록만 f에 저장
  python scripts/subtitles.py organize --dir <폴더> 받아둔 TXT를 주제별 폴더로 분류 (+ 번호 재정렬)
  python scripts/subtitles.py index                 전체 자막 목차(INDEX.md) + 검색 DB(data/subtitles.db) 생성
  python scripts/subtitles.py search "불안"         자막 본문 검색
  python scripts/subtitles.py summarize --next 1    오늘 요약할 자막 (하루 1편 큐, data/summary_queue.json)

다운로드 동작:
  1) 주소 종류를 자동 판별 (채널은 '영상' 탭으로 자동 보정)
  2) 저장 폴더를 자동 결정: authors/<이름>/subtitles
     (채널ID / .aliases / 폴더 이름으로 기존 폴더를 찾고, 없으면 새로 만듭니다. 질문 없음)
  3) 이미 받은 영상은 자동으로 건너뜀 → 채널 주소를 다시 넣으면 '새 영상만' 받습니다
     (폴더의 .downloaded_ids.txt, authors/<이름>/urls.txt, 기존 자막 제목과 대조)
  4) 자막(ko 우선, 없으면 en)을 받아 타임코드를 제거한 .txt로 저장

사전 준비:
  pip install yt-dlp --break-system-packages

사용 예:
  python scripts/subtitles.py "https://www.youtube.com/@joohankim"
  python scripts/subtitles.py "https://www.youtube.com/@joohankim" -n 1        # 최신 1개만
  python scripts/subtitles.py "https://www.youtube.com/@joohankim" --months 3  # 최근 3개월
  python scripts/subtitles.py "https://youtu.be/xxxx"                           # 단일 영상
  python scripts/subtitles.py --file "authors/Joohan Kim/urls.txt"
  python scripts/subtitles.py "<채널 URL>" --urls-only "authors/<이름>/urls.txt"
  python scripts/subtitles.py organize --dir "authors/Joohan Kim/subtitles" --dry-run

다운로드 옵션 (대부분 필요 없음):
  url                      영상 / 재생목록 / 채널 URL (생략하면 물어봄)
  --file FILE              URL이 담긴 텍스트 파일 (한 줄에 URL 하나, 제목이 붙어 있어도 됨)
  --urls-only FILE         자막은 받지 않고 영상 URL 목록만 FILE에 저장
  -n, --limit N            새 영상 중 최신 N개만 처리
  --months N / --since D   최근 N개월 / YYYY-MM-DD 이후에 올라온 영상만 처리 (채널·재생목록)
  -o, --outdir             저장 폴더를 직접 지정 (기본: 자동)
  --dry-run                받지 않고 어디에 무엇을 저장할지만 미리보기
  --all                    이미 받은 영상도 다시 받기
  --lang                   자막 언어 우선순위 (기본: ko,en)
  --auto-only              자동생성 자막만 사용
  --sleep / --retries      영상 간 대기(초) / 429 재시도 횟수
  --cookies / --cookies-from-browser   429가 계속될 때 로그인 쿠키 사용

429(Too Many Requests)가 계속되면 IP 단위 차단이므로 코드 문제가 아닙니다.
수십 분 쉬거나 --cookies-from-browser chrome 을 쓰세요. 중단 후 재실행하면 이어받습니다.

분류(organize) 참고:
  CATEGORIES는 김주환 교수님 채널 주제 기준입니다. 다른 저자에게 쓰려면 아래 CATEGORIES를 고치세요.
  같은 이름 파일이 목적지에 있으면 내용이 같을 때만 원본을 삭제하고, 다르면 건너뜁니다.
"""

import argparse
import filecmp
import html
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


# ===========================================================================
# 공용 함수: yt-dlp 호출, 파일명 정리, VTT 변환
# ===========================================================================

# 영상 ID 추출용 (watch?v= / youtu.be/ / shorts/ / embed/)
VIDEO_ID_RE = re.compile(r'(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})')

# 메타데이터/부산물 파일: 자막으로 취급하지 않습니다.
NON_SUBTITLE_FILES = {"urls.txt", "failed_urls.txt", ".downloaded_ids.txt"}


# ---------------------------------------------------------------------------
# yt-dlp
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


def require_ytdlp() -> list:
    """yt-dlp 호출 명령을 돌려줍니다. 설치돼 있지 않으면 안내 후 종료합니다."""
    cmd = get_ytdlp_cmd()
    if cmd is None:
        print("오류: yt-dlp가 설치되어 있지 않습니다.")
        print("다음 명령으로 먼저 설치해 주세요: pip install yt-dlp --break-system-packages")
        sys.exit(1)
    return cmd


def cookie_cli_args(cookies: str = None, cookies_from_browser: str = None) -> list:
    """yt-dlp CLI용 쿠키 인자."""
    if cookies:
        return ["--cookies", cookies]
    if cookies_from_browser:
        return ["--cookies-from-browser", cookies_from_browser]
    return []


def cookie_ydl_opts(cookies: str = None, cookies_from_browser: str = None) -> dict:
    """yt_dlp.YoutubeDL(옵션 dict)용 쿠키 옵션."""
    if cookies:
        return {'cookiefile': cookies}
    if cookies_from_browser:
        return {'cookiesfrombrowser': (cookies_from_browser,)}
    return {}


def is_rate_limited(stderr_text: str) -> bool:
    if not stderr_text:
        return False
    lowered = stderr_text.lower()
    return "429" in lowered or "too many requests" in lowered


# ---------------------------------------------------------------------------
# URL / 이름
# ---------------------------------------------------------------------------

def extract_video_id(url: str) -> str:
    match = VIDEO_ID_RE.search(url) or re.search(r'(?:v=|youtu\.be/|shorts/)([\w-]{6,})', url)
    return match.group(1) if match else url


def sanitize_name(name: str) -> str:
    """파일/폴더명으로 쓸 수 없는 문자를 제거/치환합니다."""
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.strip().strip(".")
    return name[:150] or "untitled"


def clean_title(title: str) -> str:
    """제목 앞뒤 공백/구분기호를 정리해서 파일명으로 쓰기 좋게 다듬습니다."""
    if not title:
        return "untitled"
    t = re.sub(r'\s+', ' ', title).strip().strip(' -_·')
    return sanitize_name(t or "untitled")


# ---------------------------------------------------------------------------
# VTT -> 순수 텍스트
# ---------------------------------------------------------------------------

def vtt_to_plain_text(vtt_path: Path) -> str:
    """VTT 자막 파일을 읽어 타임코드/태그를 제거한 순수 텍스트로 변환합니다.

    자동생성 자막은 같은 줄이 여러 번 겹쳐 나오므로 중복 줄은 한 번만 남깁니다.
    """
    lines = Path(vtt_path).read_text(encoding="utf-8", errors="ignore").splitlines()

    text_lines = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line or line.upper().startswith("WEBVTT"):
            continue
        if line.startswith(("Kind:", "Language:")) or "-->" in line:
            continue
        if re.fullmatch(r'\d+', line):  # 자막 번호(SRT 스타일)만 있는 줄
            continue
        line = html.unescape(re.sub(r'<[^>]+>', '', line)).strip()
        if not line or line in seen:
            continue
        seen.add(line)
        text_lines.append(line)

    return "\n".join(text_lines)


# ===========================================================================
# 다운로드: 주소 판별 → 폴더 결정 → 자막 받기
# ===========================================================================

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
    is_single_video = bool(re.search(r'(?:[?&]v=|youtu\.be/|/shorts/)[\w-]{11}', url))
    if is_single_video:
        # 재생목록 안의 영상 링크(&list=...)여도 '그 영상 하나'만 받습니다.
        url = re.sub(r'[?&](list|index|start_radio|pp)=[^&]*', '', url).replace('?&', '?')
    elif 'list=' in url and 'playlist?list=' not in url:
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
        'noplaylist': is_single_video,
    }
    ydl_opts.update(cookie_ydl_opts(cookies, cookies_from_browser))

    print(f"\n[안내] 주소를 분석 중입니다: {url}")
    print("[안내] 영상이 많을 경우 시간이 다소 소요될 수 있습니다...\n")

    video_urls = []
    titles = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)

        if not result:
            return None, None, None, None, video_urls, titles

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
                if entry.get('title'):
                    titles[video_url] = entry['title']

    return source_type, title, uploader, channel_id, video_urls, titles


def step1_extract(source: str, cookies: str = None, cookies_from_browser: str = None):
    print("=" * 60)
    print("1단계: 주소 판별 + 영상 목록 추출")
    print("=" * 60)

    try:
        source_type, title, uploader, channel_id, video_urls, titles = extract_source(
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

    return source_type, title, uploader, channel_id, video_urls, titles


# ---------------------------------------------------------------------------
# 저장 폴더 결정 (저장소의 authors/<이름>/subtitles 구조를 고려해 자동 생성)
# ---------------------------------------------------------------------------

CHANNEL_ID_MARKER = ".channel_id"
ALIASES_FILE = ".aliases"   # 폴더 이름 외에 제목/업로더에서 찾을 이름들 (한 줄에 하나, 예: 한글 이름)


def find_repo_authors_dir() -> Path:
    """이 스크립트가 속한 저장소에 authors/ 폴더가 있으면 그 경로를 돌려줍니다."""
    repo_root = Path(__file__).resolve().parent.parent
    authors_dir = repo_root / "authors"
    if authors_dir.is_dir():
        return authors_dir
    return None


def author_names(author_dir: Path) -> list:
    """폴더 이름 + .aliases 파일에 적힌 별칭들."""
    names = [author_dir.name]
    aliases = author_dir / ALIASES_FILE
    if aliases.is_file():
        names += [l.strip() for l in aliases.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [n for n in names if n]


def find_matching_author_folder(authors_dir: Path, channel_id: str, *text_candidates: str):
    """authors/ 밑에서 이 채널에 해당하는 기존 폴더를 찾습니다.

    1) 채널ID로 정확히 매칭 (한 번이라도 매칭된 폴더는 .channel_id에 기록해두므로,
       다음부터는 제목에 한글 이름이 없는 단일 영상이어도 정확히 찾을 수 있습니다).
    2) 채널ID로 못 찾으면, 제목/업로더 문자열 안에 기존 폴더 이름이 들어있는지로 보조 매칭합니다.
       (유튜브 메타데이터의 uploader/channel은 보통 영문 채널명이라 예: "Joohan Kim's ...",
       폴더 이름과 다를 때가 많은데, 재생목록/영상 제목에는 한글 이름이 그대로 들어있는
       경우가 많습니다. 폴더 이름은 영어로 두고, 한글 이름은 폴더 안 .aliases 파일에 적어두세요.)
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
            if any(name in cand for name in author_names(d)):
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
    """--outdir이 있으면 그대로, 없으면 질문 없이 자동으로 결정합니다."""
    if args.outdir:
        return Path(args.outdir)
    return auto_outdir(uploader, title, channel_id)


def prompt_for_url(args):
    if args.url:
        return
    if not sys.stdin.isatty():
        print("[오류] URL이 필요합니다. 예: python scripts/subtitles.py <URL>")
        sys.exit(1)
    try:
        args.url = input("영상 / 재생목록 / 채널 URL을 붙여넣으세요: ").strip().strip('"').strip("'")
    except EOFError:
        args.url = ""
    if not args.url:
        print("[종료] 입력된 URL이 없습니다.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# 2단계: 자막 다운로드
# ---------------------------------------------------------------------------

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


def collect_known_ids(outdir: Path) -> set:
    """이 저장 폴더 기준으로 이미 받았거나 목록에 올려둔 영상 ID를 모읍니다."""
    ids = set(load_done_ids(outdir))
    for f in (outdir / "urls.txt", outdir.parent / "urls.txt"):
        if f.is_file():
            ids.update(VIDEO_ID_RE.findall(f.read_text(encoding="utf-8", errors="ignore")))
    return ids


def _normalize_title(name: str) -> str:
    name = re.sub(r'^\d+[\s_.\-]+', '', name)        # 앞의 번호 접두사 제거
    return re.sub(r'[\W_]+', '', name).lower()


def collect_existing_titles(outdir: Path) -> set:
    """폴더(하위 분류 폴더 포함)에 이미 있는 자막 파일의 제목을 모읍니다."""
    if not outdir.is_dir():
        return set()
    return {_normalize_title(f.stem) for f in outdir.rglob("*.txt")
            if f.name not in NON_SUBTITLE_FILES}


def get_upload_date(url: str, cookies: str = None, cookies_from_browser: str = None):
    """영상의 업로드 날짜(YYYYMMDD)를 조회합니다. 실패하면 None."""
    import yt_dlp
    opts = {'skip_download': True, 'quiet': True, 'no_warnings': True, 'ignoreerrors': True}
    if cookies:
        opts['cookiefile'] = cookies
    elif cookies_from_browser:
        opts['cookiesfrombrowser'] = (cookies_from_browser,)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return None
    return (info or {}).get('upload_date')


def filter_since(items: list, cutoff: str, cookies=None, cookies_from_browser=None, patience: int = 3):
    """최신순 목록에서 cutoff(YYYYMMDD) 이후 영상만 남깁니다.

    채널 목록은 최신순이므로 cutoff보다 오래된 영상이 연속 patience개 나오면 조회를 멈춥니다
    (상단 고정 영상 때문에 한두 개 섞여 있어도 안전하도록).
    """
    kept, older_streak = [], 0
    for pos, u in items:
        d = get_upload_date(u, cookies, cookies_from_browser)
        if d is None or d >= cutoff:
            kept.append((pos, u))
            older_streak = 0
        else:
            older_streak += 1
            if older_streak >= patience:
                break
    return kept


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
    ydl_opts.update(cookie_ydl_opts(cookies, cookies_from_browser))

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return None

    if not info:
        return None

    auto_caps = info.get('automatic_captions') or {}

    # 최신 yt-dlp는 원본 트랙을 'ko-orig' 처럼 표시합니다.
    for lang in auto_caps:
        if lang.endswith('-orig'):
            return lang[:-len('-orig')]

    # 구버전 대비: 번역 파라미터(tlang=)가 없는 트랙이 '딱 하나'일 때만 원본으로 인정합니다.
    # (여러 개면 추측하지 않습니다 — 엉뚱한 언어를 요청해 429처럼 실패하던 원인이었습니다.)
    originals = [
        lang for lang, fmts in auto_caps.items()
        if any('tlang=' not in (f.get('url') or '') for f in fmts)
    ]
    return originals[0] if len(originals) == 1 else None


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
    """재생목록만 순서 번호를 붙이고, 채널/단일 영상은 제목만 사용합니다.

    채널은 실행할 때마다 '새 영상'만 받기 때문에 번호를 붙이면 매번 1번부터 다시 매겨져
    기존 파일과 번호가 꼬입니다.
    """
    clean = clean_title(title)
    if source_type != 'playlist' or total <= 1:
        return clean
    pad = len(str(total))
    return f"{index:0{pad}d}_{clean}"


def download_batch(items: list, total: int, outdir: Path, source_type: str, langs: str, auto_only: bool,
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

    for n, (i, url) in enumerate(items, start=1):
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
                remaining = [u for _, u in items[n:]]
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

        if n < len(items) and dynamic_sleep > 0:
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

    # 받고 나서야 알 수 있는 '진짜 제목'이 이미 있는 자막과 같으면 중복이므로 저장하지 않습니다.
    if source_type != 'video' and _normalize_title(clean_title(title)) in collect_existing_titles(outdir):
        for vf in vtt_files:
            try:
                vf.unlink()
            except OSError:
                pass
        print(f"  = 중복(이미 같은 제목의 자막이 있음)이라 저장하지 않습니다: {clean_title(title)}")
        return True, url, "중복 건너뜀", False, last_wait

    chosen = vtt_files[0]
    plain_text = vtt_to_plain_text(chosen)

    filename_stem = build_filename_stem(index, total, source_type, title)
    out_path = outdir / f"{filename_stem}.txt"
    counter = 1
    while out_path.exists() and source_type != 'video':   # 단일 영상은 같은 이름이면 덮어씁니다
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


def step2_download_subtitles(items: list, total: int, outdir: Path, source_type: str, lang: str, auto_only: bool,
                              sleep: float = 5, retries: int = 3,
                              cookies: str = None, cookies_from_browser: str = None):
    print("\n" + "=" * 60)
    print("2단계: 자막 다운로드")
    print("=" * 60)
    print(f"총 {len(items)}개의 영상을 처리합니다. 저장 폴더: {outdir.resolve()}\n")

    success_list, fail_list = download_batch(items, total, outdir, source_type, lang, auto_only,
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
URL_RE = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w\-]+[^\s]*'
    r'|youtu\.be/[\w\-]+[^\s]*|youtube\.com/shorts/[\w\-]+[^\s]*)'
)


def extract_urls_from_text(text: str) -> list:
    """텍스트에서 YouTube URL만 순서를 유지하며 중복 없이 추출합니다."""
    return list(dict.fromkeys(URL_RE.findall(text)))


# ===========================================================================
# 분류: TXT 자막을 주제별 폴더로 정리 (organize)
# ===========================================================================

# 카테고리별 키워드 정의 (순서가 중요합니다 - 위에서부터 먼저 매칭)
# 하나의 파일이 여러 키워드에 걸릴 경우, 먼저 나열된 카테고리로 분류됩니다.
CATEGORIES = [
    ("01_mental_strength_resilience", [
        "마음근력", "회복탄력성", "그릿", "그릿(", "성취역량", "동기부여",
        "자기불리화", "인정중독", "인정에 의존",
    ]),
    ("02_neuroscience_consciousness", [
        "뇌", "의식", "신경가소성", "도파민", "뇌파", "감마파", "미토콘드리아",
        "능동적 추론", "예측모형", "마코프 블랭킷",
    ]),
    ("03_emotion_psychology", [
        "불안", "분노", "용서", "사랑", "감사", "연민", "두려움", "감정",
        "트라우마", "EMDR", "최면", "플라시보",
    ]),
    ("04_meditation_theory_tradition", [
        "명상", "아나빠나사띠", "니미따", "불교", "유교", "간화선", "돈오점수",
        "알아차림", "메따", "위빠사나",
    ]),
    ("05_philosophy_thought", [
        "장자", "화엄", "공(空)", "연기(", "자유 의지", "이기적 유전자",
        "중관사상", "체화된 마음", "신라", "지눌",
    ]),
    ("06_body_sensation", [
        "소매틱", "미주신경", "고유감각", "내부감각", "알로스태시스",
        "움직임", "호흡", "심상 훈련",
    ]),
    ("07_society_media_semiotics", [
        "기호", "브랜드", "대중매체", "디지털", "미술", "세뇌", "휴대폰",
    ]),
    ("08_children_education_learning", [
        "아이", "공부", "학습", "시험", "어린이집",
    ]),
    ("09_relationships_communication", [
        "내면소통", "인간관계", "부부", "연인", "커뮤니케이션", "엄마",
        "친절", "무례",
    ]),
    ("10_health_sleep_nutrition", [
        "숙면", "잠 잘 자는 법", "식사", "운동법", "먹어야",
    ]),
]

OTHER_FOLDER = "_inbox"   # 키워드에 안 걸린 자막의 임시 보관함 (주제가 정해지면 옮김)


def renumber_folder(folder: Path, dry_run: bool = False) -> int:
    """폴더 안 파일에 가나다순으로 01_, 02_... 번호를 다시 매깁니다. 바뀐 파일 수를 돌려줍니다."""
    files = [f for f in folder.glob("*.txt") if f.is_file() and f.name not in NON_SUBTITLE_FILES]
    stems = sorted(((re.sub(r'^\d+_', '', f.name), f) for f in files), key=lambda t: t[0])
    pad = max(2, len(str(len(stems))))
    plan = [(f, folder / f"{i:0{pad}d}_{stem}") for i, (stem, f) in enumerate(stems, start=1)]
    plan = [(src, dst) for src, dst in plan if src != dst]
    if dry_run:
        return len(plan)
    # 이름이 서로 겹치지 않도록 임시 이름을 거쳐 바꿉니다.
    temps = []
    for src, dst in plan:
        tmp = src.with_name(src.name + ".renumber_tmp")
        src.rename(tmp)
        temps.append((tmp, dst))
    for tmp, dst in temps:
        tmp.rename(dst)
    return len(plan)


def classify(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    for folder_name, keywords in CATEGORIES:
        for kw in keywords:
            if kw in stem:
                return folder_name
    return OTHER_FOLDER


def run_organize(args):
    base_dir = Path(args.dir)
    if not base_dir.exists():
        sys.exit(f"오류: 폴더를 찾을 수 없습니다 - {base_dir}")

    txt_files = sorted(f for f in base_dir.glob("*.txt")
                       if f.is_file() and f.name not in NON_SUBTITLE_FILES)
    if not txt_files:
        print("정리할 TXT 파일이 없습니다.")
        return

    print(f"총 {len(txt_files)}개의 파일을 분류합니다.\n")
    plan = {}
    for f in txt_files:
        plan.setdefault(classify(f.name), []).append(f)

    for category in [c[0] for c in CATEGORIES] + [OTHER_FOLDER]:
        files = plan.get(category, [])
        if files:
            print(f"[{category}] {len(files)}개")
            for f in files:
                print(f"    - {f.name}")

    if args.dry_run:
        print("\n(--dry-run 모드이므로 실제 이동은 하지 않았습니다.)")
        return

    print("\n파일 이동을 시작합니다...")
    moved = skipped = 0
    for category, files in plan.items():
        target_dir = base_dir / category
        target_dir.mkdir(exist_ok=True)
        for f in files:
            dest = target_dir / f.name
            if dest.exists():
                if filecmp.cmp(f, dest, shallow=False):
                    f.unlink()
                    print(f"  중복 삭제 (내용 동일): {category}/{f.name}")
                else:
                    print(f"  건너뜀 (이름은 같지만 내용이 다름 - 수동 확인 필요): {category}/{f.name}")
                skipped += 1
                continue
            shutil.move(str(f), str(dest))
            moved += 1
    print(f"\n완료: {moved}개 이동, {skipped}개 건너뜀")

    # 파일이 들어온 폴더는 'NN_' 번호를 가나다순으로 다시 매깁니다.
    for category in plan:
        changed = renumber_folder(base_dir / category)
        if changed:
            print(f"  번호 재정렬: {category} ({changed}개 파일명 변경)")

    if plan.get(OTHER_FOLDER):
        print(f"\n'{OTHER_FOLDER}' 폴더로 분류된 파일은 키워드가 매칭되지 않은 항목입니다.")
        print("필요하시면 CATEGORIES에 키워드를 추가해 재분류하실 수 있습니다.")


# ===========================================================================
# 명령행
# ===========================================================================

def read_url_file(path: str) -> list:
    p = Path(path)
    if not p.exists():
        sys.exit(f"오류: 파일을 찾을 수 없습니다 - {path}")
    return extract_urls_from_text(p.read_text(encoding="utf-8", errors="ignore"))


def run_download(args):
    require_ytdlp()

    if args.file:
        # URL 목록 파일: 첫 영상의 채널 정보로 저장 폴더를 결정합니다.
        video_urls = read_url_file(args.file)
        if not video_urls:
            sys.exit("추출된 URL이 없습니다. 프로그램을 종료합니다.")
        _, title, uploader, channel_id, _, _ = extract_source(
            video_urls[0], cookies=args.cookies, cookies_from_browser=args.cookies_from_browser)
        source_type, titles = 'list', {}
        print(f"URL 목록 파일에서 {len(video_urls)}개의 영상을 읽었습니다.")
    else:
        prompt_for_url(args)
        source_type, title, uploader, channel_id, video_urls, titles = step1_extract(
            args.url, cookies=args.cookies, cookies_from_browser=args.cookies_from_browser)

    if args.urls_only:
        out = Path(args.urls_only)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(video_urls) + "\n", encoding="utf-8")
        print(f"★ 영상 URL {len(video_urls)}개를 '{out}'에 저장했습니다.")
        return

    outdir = resolve_outdir(args, uploader, title, channel_id)
    total = len(video_urls)
    print(f"저장 폴더: {outdir.resolve()}")

    # 이미 받은 영상 걸러내기 (ID 또는 제목이 같은 자막이 이미 있으면 건너뜀)
    items = list(enumerate(video_urls, start=1))
    if not args.all and source_type != 'video':   # 단일 영상은 지정한 그 영상을 항상 받습니다
        known_ids = collect_known_ids(outdir)
        known_titles = collect_existing_titles(outdir)
        fresh = []
        for pos, u in items:
            t = titles.get(u)
            if extract_video_id(u) in known_ids or (t and _normalize_title(clean_title(t)) in known_titles):
                continue
            fresh.append((pos, u))
        print(f"이미 받은 영상 {len(items) - len(fresh)}개는 건너뜁니다 → 새 영상 {len(fresh)}개")
        items = fresh

    if not items:
        print("\n새로 받을 영상이 없습니다. (모두 받은 상태입니다. 다시 받으려면 --all)")
        return

    cutoff = None
    if args.since:
        cutoff = args.since.replace("-", "")
    elif args.months:
        import datetime
        cutoff = (datetime.date.today() - datetime.timedelta(days=round(args.months * 30.44))
                  ).strftime("%Y%m%d")
    if cutoff and source_type != 'video':
        print(f"{cutoff[:4]}-{cutoff[4:6]}-{cutoff[6:]} 이후 영상만 선별하는 중...")
        before = len(items)
        items = filter_since(items, cutoff, args.cookies, args.cookies_from_browser)
        print(f"기간 필터: {before}개 → {len(items)}개")
        if not items:
            print("\n해당 기간에 새로 받을 영상이 없습니다.")
            return

    if args.limit and args.limit > 0:
        items = items[:args.limit]
        print(f"최신 {len(items)}개만 처리합니다 (-n {args.limit}).")

    if args.dry_run:
        print("\n[dry-run] 받을 영상 목록 (실제로 다운로드하지 않습니다)")
        for n, (pos, u) in enumerate(items, start=1):
            t = titles.get(u)
            stem = build_filename_stem(pos, total, source_type, t or "영상 제목")
            print(f"  [{n}/{len(items)}] {u}  ->  {stem}.txt")
        return

    # 채널ID 기록: 다음부터 제목에 이름이 없는 단일 영상도 같은 폴더로 매칭됩니다.
    authors_dir = find_repo_authors_dir()
    resolved = outdir.resolve()
    if (authors_dir is not None and resolved.name == "subtitles"
            and resolved.parent.parent == authors_dir.resolve()):
        remember_channel_id(resolved.parent, channel_id)

    outdir.mkdir(parents=True, exist_ok=True)

    success, fail = step2_download_subtitles(
        items, total, outdir, source_type, args.lang, args.auto_only,
        sleep=args.sleep, retries=args.retries,
        cookies=args.cookies, cookies_from_browser=args.cookies_from_browser)

    print("\n" + "=" * 60)
    print(f"완료: 성공 {len(success)}건 / 실패 {len(fail)}건  →  {outdir.resolve()}")
    for _, info in success:
        if info and Path(str(info)).suffix == ".txt":
            print(f"  + {Path(info).name}")
    print("=" * 60)


def build_parser():
    parser = argparse.ArgumentParser(
        description="YouTube 자막 다운로드(URL/목록 파일) 및 주제별 분류 도구",
        epilog="분류: subtitles.py organize --dir <폴더> [--dry-run] / 목차+DB: subtitles.py index / 검색: subtitles.py search <검색어>")
    parser.add_argument("url", nargs="?", help="영상 / 재생목록 / 채널 URL (생략하면 물어봅니다)")
    parser.add_argument("--url", dest="url_opt", help=argparse.SUPPRESS)  # 예전 사용법 호환
    parser.add_argument("--file", help="URL이 담긴 텍스트 파일 (한 줄에 URL 하나)")
    parser.add_argument("--urls-only", metavar="FILE", help="자막은 받지 않고 영상 URL 목록만 FILE에 저장")
    parser.add_argument("-n", "--limit", type=int, help="새 영상 중 최신 N개만 처리")
    parser.add_argument("--months", type=int, help="최근 N개월 이내에 올라온 영상만")
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="이 날짜 이후에 올라온 영상만")
    parser.add_argument("-o", "--outdir", help="저장 폴더 직접 지정 (기본: authors/<이름>/subtitles 자동)")
    parser.add_argument("--dry-run", action="store_true", help="받지 않고 계획만 출력")
    parser.add_argument("--all", action="store_true", help="이미 받은 영상도 다시 받기")
    parser.add_argument("--lang", default="ko,en", help="자막 언어 우선순위, 콤마 구분 (기본값: ko,en)")
    parser.add_argument("--auto-only", action="store_true", help="자동생성 자막만 사용")
    parser.add_argument("--sleep", type=float, default=5, help="영상 사이 최소 대기 시간(초) (기본값: 5)")
    parser.add_argument("--retries", type=int, default=3, help="429 시 영상당 재시도 횟수 (기본값: 3)")
    parser.add_argument("--cookies", help="쿠키 파일 경로 (Netscape 형식)")
    parser.add_argument("--cookies-from-browser", metavar="BROWSER",
                        help="브라우저 쿠키 사용 (예: chrome, firefox, edge)")
    return parser


# ===========================================================================
# 인덱스 / 데이터베이스: 전체 자막 목록(INDEX.md) + 검색용 SQLite(data/subtitles.db)
# ===========================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "subtitles.db"            # 재생성 가능 (git 제외)
SUMMARIES_PATH = REPO_ROOT / "data" / "summaries.jsonl"  # 요약 원본 (git 추적, 내용 해시로 연결)
INDEX_MD = REPO_ROOT / "INDEX.md"
QUEUE_PATH = REPO_ROOT / "data" / "summary_queue.json"    # 하루 1편 요약 순서


def scan_documents(authors_dir: Path) -> list:
    """authors/<저자>/subtitles/ 아래의 모든 자막 TXT를 읽어 메타데이터 목록을 만듭니다."""
    import hashlib

    docs = []
    for author_dir in sorted(d for d in authors_dir.iterdir() if d.is_dir()):
        sub = author_dir / "subtitles"
        if not sub.is_dir():
            continue
        for f in sorted(sub.rglob("*.txt")):
            if f.name in NON_SUBTITLE_FILES:
                continue
            rel = f.relative_to(sub)
            body = f.read_text(encoding="utf-8", errors="ignore")
            seq_m = re.match(r'^(\d+)_', f.name) or re.search(r'(\d+) - ', f.name)
            hangul = len(re.findall(r'[가-힣]', body))
            letters = len(re.findall(r'[A-Za-z가-힣]', body)) or 1
            docs.append({
                "author": author_dir.name,
                "category": rel.parts[0] if len(rel.parts) > 1 else "",
                "seq": int(seq_m.group(1)) if seq_m else None,
                "title": re.sub(r'^\d+_', '', f.stem),
                "path": f.relative_to(REPO_ROOT).as_posix() if f.is_relative_to(REPO_ROOT) else str(f),
                "chars": len(body),
                "lines": body.count("\n") + 1 if body else 0,
                "lang": "ko" if hangul / letters > 0.3 else "en",
                "sha1": hashlib.sha1(body.encode("utf-8")).hexdigest(),
                "body": body,
            })
    return docs


def load_summaries(path: Path = None) -> dict:
    """data/summaries.jsonl -> {내용해시: {summary, topics}}  (파일 이름이 바뀌어도 연결 유지)"""
    import json

    path = path or SUMMARIES_PATH
    out = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                out[row["sha1"]] = row
    return out


def build_database(docs: list, summaries: dict, db_path: Path = None):
    import json
    import sqlite3

    db_path = db_path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY, author TEXT, category TEXT, seq INTEGER, title TEXT,
            path TEXT UNIQUE, chars INTEGER, lines INTEGER, lang TEXT, sha1 TEXT,
            summary TEXT, topics TEXT, one_line TEXT, key_points TEXT, notion_url TEXT, summarized_at TEXT
        );
        CREATE VIRTUAL TABLE docs_fts USING fts5(title, summary, body, tokenize='trigram');
    """)
    for d in docs:
        sm = summaries.get(d["sha1"], {})
        cur = con.execute(
            "INSERT INTO documents(author,category,seq,title,path,chars,lines,lang,sha1,summary,topics,"
            "one_line,key_points,notion_url,summarized_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d["author"], d["category"], d["seq"], d["title"], d["path"], d["chars"], d["lines"],
             d["lang"], d["sha1"], sm.get("summary"), json.dumps(sm.get("topics", []), ensure_ascii=False),
             sm.get("one_line"), json.dumps(sm.get("key_points", []), ensure_ascii=False),
             sm.get("notion_url"), sm.get("summarized_at")))
        con.execute("INSERT INTO docs_fts(rowid,title,summary,body) VALUES (?,?,?,?)",
                    (cur.lastrowid, d["title"], sm.get("summary") or "", d["body"]))
    con.commit()
    con.close()


def write_index_md(docs: list, summaries: dict, out: Path = None):
    from urllib.parse import quote

    out = out or INDEX_MD
    lines = ["# 자막 인덱스", "",
             "`python scripts/subtitles.py index`로 자동 생성됩니다. 직접 수정하지 마세요.", ""]
    total_summ = sum(1 for d in docs if d["sha1"] in summaries)
    lines += [f"전체 {len(docs)}개 / 요약 {total_summ}개", ""]

    authors = sorted({d["author"] for d in docs})
    lines += ["| 저자 | 자막 수 | 글자 수 |", "|---|---:|---:|"]
    for a in authors:
        ds = [d for d in docs if d["author"] == a]
        lines.append(f"| {a} | {len(ds)} | {sum(d['chars'] for d in ds):,} |")
    lines.append("")

    for a in authors:
        lines += [f"## {a}", ""]
        cats = sorted({d["category"] for d in docs if d["author"] == a})
        for c in cats:
            ds = sorted((d for d in docs if d["author"] == a and d["category"] == c),
                        key=lambda d: (d["seq"] is None, d["seq"] or 0, d["title"]))
            if c:
                lines += [f"### {c} ({len(ds)})", ""]
            lines += ["| # | 제목 | 글자 수 | 요약 |", "|--:|---|--:|---|"]
            for d in ds:
                sm = summaries.get(d["sha1"], {})
                summ = (sm.get("one_line") or sm.get("summary") or "").replace("\n", " ").replace("|", "\\|")
                if sm.get("notion_url"):
                    summ += f" ([Notion]({sm['notion_url']}))"
                title = d["title"].replace("|", "\\|")
                link = quote(d["path"])
                lines.append(f"| {d['seq'] or ''} | [{title}]({link}) | {d['chars']:,} | {summ} |")
            lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")


def run_index(args):
    authors_dir = REPO_ROOT / "authors"
    if not authors_dir.is_dir():
        sys.exit(f"오류: authors 폴더를 찾을 수 없습니다 - {authors_dir}")
    docs = scan_documents(authors_dir)
    summaries = load_summaries()
    build_database(docs, summaries)
    write_index_md(docs, summaries)
    covered = sum(1 for d in docs if d["sha1"] in summaries)
    orphan = len(summaries) - covered
    print(f"자막 {len(docs)}개 인덱싱 완료 (요약 {covered}개 연결, 요약 없음 {len(docs) - covered}개)")
    if orphan:
        print(f"  참고: 어떤 자막과도 연결되지 않은 요약 {orphan}개가 summaries.jsonl에 있습니다 (자막 내용이 바뀐 경우)")
    print(f"  DB   : {DB_PATH.relative_to(REPO_ROOT)}")
    print(f"  목차 : {INDEX_MD.relative_to(REPO_ROOT)}")


def run_summarize(args):
    """하루 1편 요약 큐: 아직 요약이 없는 자막을 큐 순서대로 보여줍니다."""
    import json

    docs = {d["sha1"]: d for d in scan_documents(REPO_ROOT / "authors")}
    summaries = load_summaries()
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8")) if QUEUE_PATH.is_file() else []
    queued = {q["sha1"] for q in queue}
    # 큐에 없는 새 자막은 맨 뒤에 붙입니다.
    for sha, d in docs.items():
        if sha not in queued:
            queue.append({"author": d["author"], "title": d["title"], "sha1": sha, "chars": d["chars"]})
    queue = [q for q in queue if q["sha1"] in docs]
    pending = [q for q in queue if q["sha1"] not in summaries]
    done = len(queue) - len(pending)
    print(f"요약 진행: {done}/{len(queue)}편 ({done * 100 // max(len(queue), 1)}%), 남은 {len(pending)}편")
    if args.status:
        return
    for q in pending[:args.next]:
        d = docs[q["sha1"]]
        print(f"\n- [{d['author']}] {d['title']}  ({d['chars']:,}자)\n  path: {d['path']}\n  sha1: {q['sha1']}")


def run_search(args):
    import sqlite3

    if not DB_PATH.is_file():
        sys.exit("DB가 없습니다. 먼저 `python scripts/subtitles.py index`를 실행하세요.")
    con = sqlite3.connect(DB_PATH)
    q = args.query.strip()
    where, params = "", []
    if args.author:
        where = " AND d.author = ?"
        params.append(args.author)
    if len(q) >= 3:   # trigram 전문 검색 (부분 문자열 일치)
        sql = ("SELECT d.author, d.category, d.title, d.path, "
               "snippet(docs_fts, 2, '[', ']', '…', 14) FROM docs_fts "
               "JOIN documents d ON d.id = docs_fts.rowid "
               f"WHERE docs_fts MATCH ?{where} ORDER BY rank LIMIT ?")
        rows = con.execute(sql, ['"' + q.replace('"', '""') + '"', *params, args.limit]).fetchall()
    else:             # 2글자 이하는 trigram이 안 되므로 제목 LIKE로 대체
        sql = ("SELECT d.author, d.category, d.title, d.path, '' FROM documents d "
               f"WHERE d.title LIKE ?{where} LIMIT ?")
        rows = con.execute(sql, [f"%{q}%", *params, args.limit]).fetchall()
    if not rows:
        print("검색 결과가 없습니다.")
        return
    for i, (author, cat, title, path, snip) in enumerate(rows, start=1):
        print(f"{i:>2}. [{author}/{cat}] {title}\n    {path}")
        if snip:
            print(f"    …{snip.strip()}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "organize":
        p = argparse.ArgumentParser(prog="subtitles.py organize",
                                    description="자막 TXT 파일을 주제별 폴더로 정리합니다.")
        p.add_argument("--dir", default="./subtitles", help="정리할 폴더 경로")
        p.add_argument("--dry-run", action="store_true", help="실제로 이동하지 않고 미리보기만 함")
        run_organize(p.parse_args(sys.argv[2:]))
        return

    if len(sys.argv) > 1 and sys.argv[1] == "index":
        argparse.ArgumentParser(prog="subtitles.py index",
                                description="전체 자막 인덱스(INDEX.md)와 검색 DB(data/subtitles.db)를 만듭니다."
                                ).parse_args(sys.argv[2:])
        run_index(None)
        return

    if len(sys.argv) > 1 and sys.argv[1] == "summarize":
        p = argparse.ArgumentParser(prog="subtitles.py summarize", description="하루 1편 요약 큐를 보여줍니다.")
        p.add_argument("--next", type=int, default=1, help="다음에 요약할 자막 개수 (기본값: 1)")
        p.add_argument("--status", action="store_true", help="진행률만 출력")
        run_summarize(p.parse_args(sys.argv[2:]))
        return

    if len(sys.argv) > 1 and sys.argv[1] == "search":
        p = argparse.ArgumentParser(prog="subtitles.py search", description="자막 본문/제목/요약을 검색합니다.")
        p.add_argument("query", help="검색어 (3글자 이상은 본문 전체 검색, 그 미만은 제목만)")
        p.add_argument("-a", "--author", help="저자 폴더 이름으로 제한 (예: 'Joohan Kim')")
        p.add_argument("-n", "--limit", type=int, default=10, help="최대 결과 수 (기본값: 10)")
        run_search(p.parse_args(sys.argv[2:]))
        return

    args = build_parser().parse_args()
    args.url = args.url or args.url_opt
    run_download(args)


if __name__ == "__main__":
    main()
