# 주간 신규 자막 절차 (제갈건 채널)

매주 제갈건 유튜브 채널에서 아직 없는 최신 '장자 길라잡이' 1편의 자막을 받아 요약하고 노션에 정리한다.

1. `main`을 최신으로 받는다. 채널 주소는 `authors/Jegal Geon/.channel_url`에 있으면 쓴다. 없으면 웹 검색으로 '제갈건' 채널의 '장자 길라잡이' 영상을 찾아 채널이 맞는지 확인한 뒤 그 파일에 저장한다. 확인하지 못하면 추측하지 말고 실패를 보고한다.
2. 채널의 최신 '장자 길라잡이' 영상 중 `db/lectures.json`(`items`, `notion_only`)에도, 노션 부모 페이지의 하위 페이지에도 없는 가장 낮은 회차를 고른다. 새 영상이 없으면 그렇게 보고하고 끝낸다.
3. 자막을 받는다. 유튜브 링크는 `youtube-transcript-summary` 스킬로 처리한다. `yt-dlp`가 막히면 `web_embedded` 방식(`--extractor-args "youtube:player_client=web_embedded"`)으로 다시 시도한 뒤에만 실패를 보고한다. `scripts/auto_subtitle_downloader.py <영상 URL>`을 쓸 수도 있다. 파일은 `subtitles/zhuangzi_guide/NNN - 제목.txt`로 저장한다.
4. `lectures.json`의 `items`에 새 항목을 추가한 뒤 `db/DAILY.md`의 2~7번과 같은 방식으로 요약하고, 노션에 병합·정리하고, `INDEX.md`를 갱신하고, 커밋·병합·푸시한다.
5. 영상 링크는 노션 페이지의 '강의 정보'에 적는다.
