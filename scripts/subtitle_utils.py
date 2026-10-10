"""자막 스크립트들이 함께 쓰는 공용 함수 모음 (yt-dlp 호출, 파일명 정리, VTT 변환)."""

import html
import re
import shutil
import sys
from pathlib import Path

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
