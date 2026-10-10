# study_joohankim

유튜브 강의 자막을 받아 주제별로 정리해두는 개인 학습 아카이브입니다.
처음에는 김주환 교수님 채널로 시작했지만, 다른 강의/저자/교수님으로도
계속 확장할 수 있도록 구조를 잡았습니다.

## 폴더 구조

폴더 이름은 모두 영어(ASCII)로 통일합니다. 파일 이름(영상 제목)은 원문 그대로 둡니다.

```
.
├── scripts/                        # 자막 다운로드 / 분류 도구 (저자 무관, 공용)
│   ├── auto_subtitle_downloader.py    # (권장) URL 하나로 영상/재생목록/채널 자동 처리
│   ├── yt_subtitle_downloader.py      # URL 목록 파일(urls.txt)로 일괄 다운로드
│   ├── get_youtube_urls.py            # 채널/재생목록의 영상 URL 목록만 추출
│   ├── organize_subtitles.py          # TXT 자막을 주제별 폴더로 분류 (김주환 기준 카테고리)
│   ├── subtitle_utils.py              # 위 스크립트들이 공유하는 공용 함수
│   └── README.md
└── authors/                        # 저자(채널)별 자막 아카이브
    └── <이름>/
        ├── .channel_id                # 채널ID (폴더 자동 매칭용, 다운로더가 생성)
        ├── .aliases                   # 제목/업로더에서 찾을 다른 이름들 (예: 한글 이름, 선택)
        ├── urls.txt                   # 영상 URL 목록 (있을 때만)
        ├── README.md                  # 저자 소개 + 카테고리 설명 (선택)
        └── subtitles/                 # 자막 TXT (주제 폴더로 나뉘어 있기도 함)
            ├── .downloaded_ids.txt       # 이미 받은 영상 ID (이어받기용)
            └── failed_urls.txt           # 다운로드 실패 목록 (있을 때만)
```

현재 저자: 김주환(`Joohan Kim`), 제갈건(`Jegal Geon`), `Nathaniel Drew`, `Bryan Johnson`, `Andrew Huberman`.

- Joohan Kim은 `01_sleep_meditation` ~ `12_misc`, `summaries`, `core_six` 폴더로 주제별 분류되어 있습니다.
- Jegal Geon은 `zhuangzi_guide/` 시리즈 폴더, 나머지 저자는 폴더 분류 없이 `subtitles/`에 바로 둡니다.
- 재생목록으로 받은 파일은 `NN_제목.txt`처럼 순서 번호가 붙습니다.
- 다운로드 중 임시 VTT는 `subtitles/_tmp_vtt/`에 만들어졌다가 지워지며, `.gitignore`에 등록되어 있습니다.

## 사용법

저장소 루트에서 실행합니다.

```bash
pip install yt-dlp --break-system-packages

# 1. (권장) URL만 넣으면 끝 — 채널이면 새 영상만, 단일 영상이면 그 영상만, 저장 폴더는 자동
python scripts/auto_subtitle_downloader.py "<채널/재생목록/영상 URL>"

# 1b. URL 목록 파일로 일괄 다운로드
python scripts/yt_subtitle_downloader.py --file "authors/Joohan Kim/urls.txt" --outdir "authors/Joohan Kim/subtitles"

# 1c. 자막은 받지 않고 영상 URL 목록만 뽑기
python scripts/get_youtube_urls.py "<채널/재생목록 URL>" -o "authors/Joohan Kim/urls.txt"

# 2. 다운로드된 자막을 주제별 폴더로 자동 분류
python scripts/organize_subtitles.py --dir "authors/Joohan Kim/subtitles" --dry-run   # 미리보기
python scripts/organize_subtitles.py --dir "authors/Joohan Kim/subtitles"            # 실제 이동
```

각 스크립트의 자세한 옵션과 동작(임시 `_tmp_vtt` 처리, 언어 우선순위, 429 재시도 정책 등)은
[scripts/README.md](scripts/README.md)와 각 파일 상단의 docstring을 참고하세요.

## 새로운 저자/교수님 추가하기

1. `python scripts/auto_subtitle_downloader.py "<채널 URL>"`을 실행하면 `authors/<이름>/subtitles`가 자동으로 만들어집니다.
   (직접 지정하려면 `-o authors/<이름>/subtitles`)
2. 목록 파일로 받고 싶다면 `authors/<이름>/urls.txt`에 URL을 넣고 `yt_subtitle_downloader.py --file`을 사용합니다.
3. `scripts/organize_subtitles.py`의 `CATEGORIES`는 김주환 교수님 강의 주제에 맞춰져 있으므로,
   새 저자의 강의 주제에 맞게 카테고리/키워드를 수정하거나 별도 분류 스크립트를 만들어 사용하세요.
4. `authors/<이름>/README.md`에 채널 소개와 카테고리 설명을 간단히 남겨두면 좋습니다.

## 참고

자막 텍스트는 원 저작자(강연자)에게 저작권이 있는 콘텐츠입니다. 이 저장소는 개인 학습/검색
목적의 정리 아카이브이며, 상업적 이용이나 재배포 목적이 아닙니다.
