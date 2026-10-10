# 김주환 (Joohan Kim)

김주환 교수님의 유튜브 강의 자막을 주제별로 정리한 아카이브입니다.

- `urls.txt` — 다운로드 대상 유튜브 영상 URL 목록
- `subtitles/` — 주제별로 분류된 자막 TXT 파일 (총 191개: 카테고리 175 + summaries 10 + core_six 6)
  - 다운로드 실패 목록(`failed_urls.txt`)은 있을 때만 이 폴더에 생성됩니다.

## 카테고리

| 폴더 | 주제 | 개수 |
|---|---|---:|
| 01_sleep_meditation | 수면유도 명상 시리즈 | 30 |
| 02_mental_strength_resilience | 마음근력, 회복탄력성, 그릿, 동기부여 | 19 |
| 03_neuroscience_consciousness | 뇌, 의식, 신경가소성, 도파민, 뇌파 | 19 |
| 04_emotion_psychology | 불안, 분노, 용서, 사랑, 감사, 트라우마 | 18 |
| 05_meditation_theory_tradition | 명상, 불교, 위빠사나, 알아차림 | 19 |
| 06_philosophy_thought | 장자, 화엄, 자유 의지, 이기적 유전자 | 7 |
| 07_body_sensation | 소매틱, 미주신경, 고유감각, 호흡, 몸·마음 | 8 |
| 08_society_media_semiotics | 기호, 브랜드, 대중매체, 디지털 | 10 |
| 09_children_education_learning | 아이, 공부, 학습, 시험 | 2 |
| 10_relationships_communication | 내면소통, 인간관계, 부부, 커뮤니케이션 | 10 |
| 11_health_sleep_nutrition | 숙면, 식사, 운동법 | 4 |
| 12_misc | 아직 키워드가 매칭되지 않은 자막 | 29 |

분류 기준(키워드)은 [scripts/organize_subtitles.py](../../scripts/organize_subtitles.py)의 `CATEGORIES`에 정의되어 있습니다.
`12_misc`에 새 파일이 쌓이면 그 파일들의 제목을 보고 필요한 키워드를 `CATEGORIES`에 추가한 뒤
`organize_subtitles.py`를 재실행해 재분류할 수 있습니다.

`02_mental_strength_resilience`부터 `12_misc`까지는 폴더 안에서 파일명 가나다순으로 `01_`, `02_`... 번호를
붙여 정렬해두었습니다. `summaries`도 동일한 `01_`, `02_`... 번호 체계를 씁니다.

`01_sleep_meditation`은 제목 자체에 포함된 회차 번호(1~31, 23회 결번)를 2자리로 통일해
`수면유도 명상 01 - 제목.txt` 형태로 정렬했습니다.

`core_six`는 여러 카테고리에 걸쳐 있는 핵심 자막 6개를 모아둔 별도의 하이라이트 모음이며,
`01_`~`06_` 번호를 붙여 정리했습니다.
