# scripts

저자(교수님)에 상관없이 공용으로 쓰는 도구 모음입니다. 모두 저장소 루트에서 실행하는 것을 기준으로 합니다.

## auto_subtitle_downloader.py (권장 — URL만 넣으면 끝)

```bash
python scripts/auto_subtitle_downloader.py "<URL>"
```

- **채널 URL** → 그 채널의 영상을 전부 받습니다 (이미 받은 영상은 자동으로 건너뛰므로 다시 실행하면 새 영상만 받음).
- **단일 영상 URL** → 딱 그 영상 하나만 받습니다 (`&list=` 가 붙어 있어도 한 개만).
- **재생목록 URL** → 재생목록 전체를 순서 번호를 붙여 받습니다.
- 저장 위치는 질문 없이 `authors/<이름>/subtitles`로 자동 결정됩니다 (기존 폴더는 채널ID/제목으로 매칭).
- 자주 쓰는 옵션: `-n 1`(최신 1개만), `--dry-run`(미리보기), `--all`(다시 받기), `-o 폴더`(저장 위치 지정).
- 429가 계속되면 `--cookies-from-browser chrome`을 붙이세요.

## yt_subtitle_downloader.py

URL 목록 파일(또는 `--url`)로 여러 영상의 자막을 받아 타임코드를 제거한 순수 텍스트(.txt)로 저장합니다.
한국어 수동 자막을 우선 사용하고, 없으면 자동생성 자막을 사용합니다.

```bash
pip install yt-dlp --break-system-packages

# URL 목록 파일로 실행
python scripts/yt_subtitle_downloader.py --file "authors/Joohan Kim/urls.txt" --outdir "authors/Joohan Kim/subtitles"

# URL을 직접 지정
python scripts/yt_subtitle_downloader.py --url "https://www.youtube.com/watch?v=xxxx"

# 언어 우선순위 지정 (콤마 구분)
python scripts/yt_subtitle_downloader.py --file urls.txt --outdir out --lang ko,en
```

다운로드에 실패한 URL은 `<outdir>/failed_urls.txt`에 사유와 함께 기록됩니다.

## organize_subtitles.py

폴더 안의 자막 TXT 파일들을 제목 키워드 기준으로 주제별 하위 폴더로 이동시킵니다.
이동이므로 재실행해도 안전합니다 — 목적지에 같은 이름의 파일이 이미 있으면 내용을 비교해서,
내용이 같으면 원본(중복)을 삭제하고, 내용이 다르면 건너뛰고 수동 확인이 필요하다고 알려줍니다.
`failed_urls.txt`, `.downloaded_ids.txt`처럼 자막이 아닌 부산물 파일은 분류 대상에서 제외됩니다.
어떤 카테고리에도 안 걸리는 파일은 `12_misc` 폴더로 모입니다.

```bash
python scripts/organize_subtitles.py --dir "authors/Joohan Kim/subtitles" --dry-run   # 미리보기만
python scripts/organize_subtitles.py --dir "authors/Joohan Kim/subtitles"            # 실제 이동
```

`CATEGORIES`는 김주환 교수님 채널 주제 기준으로 작성되어 있습니다. 다른 저자의
강의를 분류할 때는 파일 상단의 `CATEGORIES`를 그 저자의 주제에 맞게 고쳐 쓰거나,
`authors/<이름>/` 전용 분류 스크립트를 따로 만들어 쓰세요.

## get_youtube_urls.py

채널/재생목록의 영상 URL만 뽑아 파일로 저장합니다 (자막은 받지 않음). 저장한 파일은
`yt_subtitle_downloader.py --file`로 넘길 수 있습니다. 주소 판별은 `auto_subtitle_downloader.py`와 같은 로직을 씁니다.

```bash
python scripts/get_youtube_urls.py "<채널/재생목록 URL>" -o "authors/Joohan Kim/urls.txt"
```

## subtitle_utils.py

위 스크립트들이 공유하는 공용 모듈입니다 (yt-dlp 호출 방식 탐색, 쿠키 옵션, 파일명 정리,
VTT → 텍스트 변환, 영상 ID 추출). 직접 실행하는 파일이 아닙니다.
