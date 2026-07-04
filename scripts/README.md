# scripts

저자(교수님)에 상관없이 공용으로 쓰는 도구 두 개입니다. 모두 저장소 루트에서 실행하는 것을 기준으로 합니다.

## yt_subtitle_downloader.py

유튜브 URL(들)의 자막을 받아 타임코드를 제거한 순수 텍스트(.txt)로 저장합니다.
한국어 수동 자막을 우선 사용하고, 없으면 자동생성 자막을 사용합니다.

```bash
pip install yt-dlp --break-system-packages

# URL 목록 파일로 실행
python scripts/yt_subtitle_downloader.py --file authors/김주환/urls.txt --outdir authors/김주환/subtitles

# URL을 직접 지정
python scripts/yt_subtitle_downloader.py --url "https://www.youtube.com/watch?v=xxxx"

# 언어 우선순위 지정 (콤마 구분)
python scripts/yt_subtitle_downloader.py --file urls.txt --outdir out --lang ko,en
```

다운로드에 실패한 URL은 `<outdir>/failed_urls.txt`에 사유와 함께 기록됩니다.

## organize_subtitles.py

폴더 안의 자막 TXT 파일들을 제목 키워드 기준으로 주제별 하위 폴더로 이동시킵니다.
이동이므로 재실행해도 안전하며(이미 있는 파일은 건너뜀), 어떤 카테고리에도
안 걸리는 파일은 `12_기타` 폴더로 모입니다.

```bash
python scripts/organize_subtitles.py --dir authors/김주환/subtitles --dry-run   # 미리보기만
python scripts/organize_subtitles.py --dir authors/김주환/subtitles            # 실제 이동
```

`CATEGORIES`는 김주환 교수님 채널 주제 기준으로 작성되어 있습니다. 다른 저자의
강의를 분류할 때는 파일 상단의 `CATEGORIES`를 그 저자의 주제에 맞게 고쳐 쓰거나,
`authors/<이름>/` 전용 분류 스크립트를 따로 만들어 쓰세요.
