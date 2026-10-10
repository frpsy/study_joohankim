#!/usr/bin/env python3
"""
채널/재생목록의 영상 URL 목록만 뽑아서 텍스트 파일로 저장합니다 (자막은 받지 않음).

  python scripts/get_youtube_urls.py "<채널/재생목록 URL>" -o authors/<이름>/urls.txt

URL을 생략하면 물어봅니다. 저장한 파일은 yt_subtitle_downloader.py --file 로 넘길 수 있습니다.
주소 판별/추출 로직은 auto_subtitle_downloader.py의 extract_source를 그대로 사용합니다.
"""

import argparse
import sys
from pathlib import Path

from auto_subtitle_downloader import SOURCE_TYPE_LABEL, extract_source
from subtitle_utils import require_ytdlp


def main():
    parser = argparse.ArgumentParser(description="채널/재생목록의 영상 URL 목록을 파일로 저장합니다.")
    parser.add_argument("url", nargs="?", help="채널 / 재생목록 URL (생략하면 물어봅니다)")
    parser.add_argument("-o", "--output", default="youtube_urls.txt", help="저장할 파일 (기본값: youtube_urls.txt)")
    parser.add_argument("--cookies", help="쿠키 파일 경로 (Netscape 형식)")
    parser.add_argument("--cookies-from-browser", metavar="BROWSER", help="브라우저 쿠키 사용 (예: chrome)")
    args = parser.parse_args()

    require_ytdlp()
    url = args.url or input("수집할 유튜브 재생목록(또는 채널) 주소를 입력하세요: ").strip()
    if not url:
        sys.exit("[종료] 입력된 주소가 없어 프로그램을 종료합니다.")

    source_type, title, uploader, _, video_urls, _ = extract_source(
        url, cookies=args.cookies, cookies_from_browser=args.cookies_from_browser
    )
    if not video_urls:
        sys.exit("[실패] 추출된 영상 URL이 없습니다. 주소를 확인해주세요.")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(video_urls) + "\n", encoding="utf-8")

    label = SOURCE_TYPE_LABEL.get(source_type, "알 수 없음")
    print("-" * 50)
    print(f"★ {label} ({title or uploader or '제목 없음'}): {len(video_urls)}개 영상 URL을 '{out}'에 저장했습니다.")
    print("-" * 50)


if __name__ == "__main__":
    main()
