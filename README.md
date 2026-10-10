# study_joohankim

유튜브 강의 자막을 받아 주제별로 정리해두는 개인 학습 아카이브입니다.
처음에는 김주환 교수님 채널로 시작했지만, 다른 강의/저자/교수님으로도
계속 확장할 수 있도록 구조를 잡았습니다.

## 폴더 구조

```
.
├── scripts/                        # 자막 다운로드 / 자동 분류 도구 (저자 무관, 공용)
│   ├── yt_subtitle_downloader.py      # 단일/여러 URL을 받아 자막 TXT로 저장
│   ├── auto_subtitle_downloader.py    # 영상/재생목록/채널 자동 판별 + 저자 폴더 자동 매칭
│   ├── get_youtube_urls.py            # 채널/재생목록의 영상 URL 목록 추출
│   ├── organize_subtitles.py          # TXT 자막을 주제별 폴더로 분류
│   └── README.md
└── authors/                        # 저자별 강의 자막 아카이브
    ├── 김주환/                        # README.md, urls.txt, subtitles/(주제별 01~12 + 요약본 + 핵심6가지)
    ├── 제갈건/
    ├── Andrew Huberman/
    ├── Bryan Johnson/
    └── Nathaniel Drew/
        └── subtitles/               # 각 저자의 자막 TXT (.channel_id = 채널 매칭용 마커)

※ 다운로드 중 생기는 임시 VTT는 `_tmp_vtt/`에 만들어지며 `.gitignore`에 등록되어 있습니다.
   `.downloaded_ids.txt`는 이어받기용 기록이므로 지우지 마세요.
```

## 사용법

저장소 루트에서 실행합니다.

```bash
pip install yt-dlp --break-system-packages

# 1. URL 목록으로 자막 다운로드 (단일/여러 URL용)
python scripts/yt_subtitle_downloader.py --file authors/김주환/urls.txt --outdir authors/김주환/subtitles

# 1b. 채널/재생목록 자동 처리 (대용량/자동화용)
python scripts/auto_subtitle_downloader.py --url "<채널/재생목록/영상 URL>" --outdir authors/김주환/subtitles

# 2. 다운로드된 자막을 주제별 폴더로 자동 분류
python scripts/organize_subtitles.py --dir authors/김주환/subtitles --dry-run   # 미리보기
python scripts/organize_subtitles.py --dir authors/김주환/subtitles            # 실제 이동
```

각 스크립트의 자세한 옵션과 동작(임시 `_tmp_vtt` 처리, 언어 우선순위, 429 재시도 정책 등)은
[scripts/README.md](scripts/README.md)와 각 파일 상단의 docstring을 참고하세요.

## 새로운 저자/교수님 추가하기

1. `authors/<이름>/` 폴더를 만들고 `urls.txt`에 해당 채널의 유튜브 URL을 넣습니다.
2. 위 다운로드 명령을 `--outdir authors/<이름>/subtitles`로 실행합니다.
3. `scripts/organize_subtitles.py`의 `CATEGORIES`는 김주환 교수님 강의 주제에 맞춰져 있으므로,
   새 저자의 강의 주제에 맞게 카테고리/키워드를 수정하거나 별도 분류 스크립트를 만들어 사용하세요.
4. `authors/<이름>/README.md`에 채널 소개와 카테고리 설명을 간단히 남겨두면 좋습니다.

## 참고

자막 텍스트는 원 저작자(강연자)에게 저작권이 있는 콘텐츠입니다. 이 저장소는 개인 학습/검색
목적의 정리 아카이브이며, 상업적 이용이나 재배포 목적이 아닙니다.
