---
name: lecture-study
description: 내면의 서재(frpsy/study_joohankim)에 강의를 추가하거나 핵심 요약·타임스탬프를 작성·검수할 때 사용
---

# 강의 추가·수정 절차

기준 문서: `AGENTS.md`(구성·검증) → `편집규칙.md`(문장·타임스탬프·자막 규칙). 이전 판(마인드맵·상세 해설 시기)은 `docs/archive/lecture-study-SKILL-2026-11-06.md`.

## 새 강의
1. 영상 ID를 먼저 확정한다(확인 안 된 ID를 만들지 않는다).
2. 자막 확보(편집규칙 8절 순서). 원문 그대로 `transcripts/<영상ID>.<언어>.txt`(+SRT/VTT)로 저장한다. 아직 없으면 편집규칙 10절대로 `caption-queue/<영상ID>.json`과 2시간 재확인으로 관리한다.
3. 자막 전 구간과 설명란을 읽고, 읽은 범위를 `study-audits/<영상ID>.json`에 기록한다.
4. `lectures.json` 맨 앞(최신순)에 등록: `id`, `date`, `title`, `duration`, `description`, `tags`, `creator`, `kind`(lecture), 필요 시 `video_url`.
5. `data/mini_courses.json`에 `lead`(한 문장)·`three`(세 문장) 작성 — 편집규칙 2·3절 기준.
6. `data/lecture_compact.json`에 — 김주환 강의: `timeline`(편집규칙 4절 형식). 그 외 강연자: `timeline` 없이 `detail`(자막 기반 상세 요약, 필요 시 웹 보충은 `[보충]` 표시, 편집규칙 14절). 공통: `sources`(label·url, 실제 확인한 링크만), 필요 시 `note`·`aliases`.
7. `build-info.json` 버전을 올리고 `build_library.py`, `build_compact_lectures.py` 실행.
8. 김주환 외 강의는 편집규칙 14절의 자체 검수(사실·출처, 문장·문법, 형식)를 끝낸다. AGENTS.md의 검증 명령 전부 통과 → PR(네 제목) → CI → 머지 → 공개 페이지에서 새 문구 확인 → 링크 보고.

## 기존 요약 다듬기
- `mini_courses.json`만 고치고 재생성한다. 뜻을 바꾸는 수정은 저장된 자막·`data/summaries.json` 원고로 근거를 확인한다.
- 비문·어색한 연결·같은 서술어 반복을 없애고, 처음 읽는 사람도 바로 이해되게 쓴다.
- 타임스탬프 원문·연구 수치·직접 인용은 문체를 이유로 고치지 않는다.

## 김주환 외 강의
- 타임스탬프 금지, `detail`로 상세 요약. 사족 없이 쓰고 출처를 남긴다. 보고 전 사실·출처 검수와 문장·문법 검수를 끝낸다(편집규칙 14절).

## 자주 걸리는 검사
- `tests/test_korean_leads.py`: lead는 문장부호 1개, ‘다.’로 끝, 55–170자, 생성 HTML과 일치.
- `tests/test_compact_courses.py`: three는 3개, 모두 ‘다.’로 끝, 머리말 금지.
- Playwright: 한 문장 글자 ≤17px, 목록 ≤16px, 제목 위계 h1>h2>h3, 가로 넘침 없음.
