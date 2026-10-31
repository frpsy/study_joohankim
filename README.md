# study_joohankim

유튜브 강의 자막을 받아 주제별로 정리해두는 개인 학습 아카이브이다.
처음에는 김주환 교수님 채널로 시작했지만, 다른 강의/저자/교수님으로도
계속 확장할 수 있도록 구조를 잡았다.

## 폴더 구조

폴더 이름은 모두 영어(ASCII)로 통일한다. 파일 이름(영상 제목)은 원문 그대로 둔다.

```
.
├── INDEX.md                        # 전체 자막 목차 (자동 생성)
├── data/subtitles.db               # 검색용 SQLite (자동 생성, git 제외)
├── scripts/
│   ├── subtitles.py                   # 다운로드 / URL 추출 / 분류 / 목차·검색을 한 파일로 처리
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

이번 정리 대상인 김주환(`Joohan Kim`)과 `Andrew Huberman` 자막은 각각 5개씩, 두 저자 합계 10개이다. 원격에 있던 다른 저자 자료는 보존한다.

- 김주환: 정리 직전 보유 자막 45개의 현재 조회수를 비교해 상위 5개를 남겼다.
- Andrew Huberman: 채널 인기 강의 상위 5개의 영어 자막을 새로 받았다.
- 제갈건 자막은 제거했다.
- 조회수 확인일: 2026-10-30. 영상별 조회수와 선정 근거는 [data/retained_top5.json](data/retained_top5.json)에 있다.
- `urls.txt`와 `.downloaded_ids.txt`는 남긴 영상만 가리킨다.
- 채널 전체 다운로드는 자막을 다시 늘린다. 현재 5개 구성을 유지하려면 저자별 `urls.txt`를 사용하세요.

## 사용법

저장소 루트에서 실행한다. 자세한 옵션은 [scripts/README.md](scripts/README.md)를 참고하세요.

```bash
pip install yt-dlp --break-system-packages

# 1. 자막 다운로드 — URL만 넣으면 끝 (채널이면 새 영상만, 단일 영상이면 그 영상만, 저장 폴더는 자동)
python scripts/subtitles.py "<채널/재생목록/영상 URL>"

# 1b. URL 목록 파일로 일괄 다운로드 / 영상 URL 목록만 뽑기
python scripts/subtitles.py --file "authors/Joohan Kim/urls.txt"
python scripts/subtitles.py "<채널/재생목록 URL>" --urls-only "authors/Joohan Kim/urls.txt"

# 2. 다운로드된 자막을 주제별 폴더로 자동 분류
python scripts/subtitles.py organize --dir "authors/Joohan Kim/subtitles" --dry-run   # 미리보기
python scripts/subtitles.py organize --dir "authors/Joohan Kim/subtitles"            # 실제 이동

# 3. 전체 목차(INDEX.md) + 검색 DB 생성, 본문 검색
python scripts/subtitles.py index
python scripts/subtitles.py search "불안감"
```

## 새로운 저자/교수님 추가하기

1. `python scripts/subtitles.py "<채널 URL>"`을 실행하면 `authors/<이름>/subtitles`가 자동으로 만들어진다.
   (직접 지정하려면 `-o authors/<이름>/subtitles`)
2. 목록 파일로 받고 싶다면 `authors/<이름>/urls.txt`에 URL을 넣고 `subtitles.py --file`을 사용한다.
3. `scripts/subtitles.py`의 `CATEGORIES`는 김주환 교수님 강의 주제에 맞춰져 있으므로,
   새 저자의 강의 주제에 맞게 카테고리/키워드를 수정하거나 별도 분류 스크립트를 만들어 사용하세요.
4. `authors/<이름>/README.md`에 채널 소개와 카테고리 설명을 간단히 남겨두면 좋다.

## 참고

자막 텍스트는 원 저작자(강연자)에게 저작권이 있는 콘텐츠이다. 이 저장소는 개인 학습/검색
목적의 정리 아카이브이며, 상업적 이용이나 재배포 목적이 아니다.

## 강의 학습 웹 편집

학습 웹과 노션 아카이브를 수정할 때 [편집규칙.md](편집규칙.md)와 [용어집.md](용어집.md)를 따른다. 에이전트 작업의 시작 지침은 [AGENTS.md](AGENTS.md)에 있다. 자막·슬라이드의 핵심을 먼저 정리하고 관련 화면과 해설을 통합하며, 전 구간 대조·수정·공개 배포 확인까지 마친 뒤 완료를 보고한다.
