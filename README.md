# 내면의 서재

강의의 핵심 결론·미니강좌·5분 요약·원본 타임라인을 읽는 **로그인 없는 정적 학습 사이트**입니다. 김주환 교수뿐 아니라 다른 강연자와 향후 책·연구 자료까지 다룰 수 있도록 구성되어 있습니다.

- **웹:** https://frpsy.github.io/study_joohankim/
- **공개 경로:** `index.html`, `concepts.html`, `lectures/<id>.html`, `mini-courses/<id>.html`, `summaries/<id>.html`
- **기능:** 자료 검색·필터, 대표 강의, 한 문장 핵심 결론, 핵심 3가지, 펼치는 5분 요약, 미니강좌, 원본 YouTube 링크, 타임라인 복사, 정적 오프라인 캐시
- **없는 기능:** 사용자 로그인, 개인 학습 기록 저장, 학습 완료 상태, 학습 이력, Firebase 연결

## 코드와 데이터의 역할

| 경로 | 책임 |
| --- | --- |
| `lectures.json` | 강의 ID·제목·출처·길이·태그 |
| `materials.json` | 향후 책·논문·글·노트 목록 |
| `data/mini_courses.json` | **한 문장 핵심 결론의 단일 원본**, 핵심 3가지, 미니강좌 |
| `data/summaries.json` | 5분 요약의 본문·적용·근거 한계 (한 문장 핵심 중복 저장 금지) |
| `data/lecture_compact.json` | 댓글 타임라인과 출처 링크 |
| `scripts/content_registry.py` | 소스 검증과 요약 데이터 결합 |
| `scripts/build_library.py` | 홈과 공통 레이아웃, `build-info.json` 버전의 정적 자산 URL |
| `scripts/build_compact_lectures.py` | 강의 노트·미니강좌 생성 |
| `scripts/build_summaries.py` | 5분 요약 생성 |
| `assets/site.css`, `assets/site.js` | 공통 디자인과 검색·복사·버전 확인 |
| `sw.js` | 동일 출처 정적 리소스 캐싱 |
| `build-info.json` | **배포·캐시 버전의 단일 원본** |

기존 콘텐츠 ID와 공개 주소를 바꾸지 않으며, 생성된 HTML은 **직접 편집하지 않습니다.**

## 변경 및 검증

저장소 루트에서 아래 순서로 실행합니다. 별도 데이터베이스나 로그인은 필요하지 않습니다.

```bash
python3 scripts/content_registry.py
python3 scripts/build_library.py
python3 scripts/build_compact_lectures.py
python3 scripts/build_summaries.py
python3 scripts/build_library.py --check
python3 scripts/build_compact_lectures.py --check
python3 scripts/build_summaries.py --check
python3 scripts/validate_design_system.py
python3 scripts/validate_site.py
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_*.cjs
```

브라우저 검사는 GitHub Actions에서 Chromium/Playwright로 자동 실행합니다. 강의 원고를 수정할 때는 데이터에서 고치고 세 생성기를 다시 실행하세요. 정적 화면 버전이 바뀌면 **`build-info.json.version`만 올리고** 생성된 HTML과 `concepts.html`의 자산 URL을 맞춥니다.

## 강의 추가

1. 실제 자막 및 원본 영상 ID·URL을 검증하고 `lectures.json`에 안정적인 콘텐츠 ID를 추가합니다. 영상 ID가 불확실하면 임의의 11자리 ID를 만들지 않습니다.
2. `data/mini_courses.json`에 한 문장 핵심 결론·핵심 3가지·미니강좌를 작성합니다.
3. `data/summaries.json`에 상세 해설·적용·근거의 한계를 작성하고, `data/lecture_compact.json`에 **실제 자막에 맞춘** 댓글 타임라인·출처를 등록합니다.
4. 위 생성·검증 명령을 실행하고 GitHub Pages 공개 URL까지 확인합니다. 한 문장 핵심 결론과 타임라인은 임의로 생성·추측하지 않습니다.

## 자막 자료 아카이브

`authors/`는 강연자별 원본 자막 아카이브입니다. 자막 확보에 **vidIQ는 사용하지 않습니다.** 저자별 수집·목차 생성 등 별도 작업은 [scripts/README.md](scripts/README.md)를 참고합니다. 원본 강의·자막의 저작권과 출처를 존중합니다.

편집 지침은 [AGENTS.md](AGENTS.md), [편집규칙.md](편집규칙.md), [디자인 계약](docs/design-system.md), [콘텐츠 모델](docs/content-model.md)을 참고합니다.
