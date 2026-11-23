# IRIS 공지 HTML skill (iris-notice-html)

IRIS 게시판에 붙여넣을 HTML 공지를 만드는 skill입니다.
IRIS 에디터는 붙여넣은 HTML의 앞부분을 미리보기로 긁어 가고, 여백·행간·제목 서식을 강제로 바꿉니다. 이 skill은 「IRIS 공지 HTML 작성 규칙」을 지켜서 미리보기에는 한글 요약이 잡히고 디자인은 깨지지 않는 HTML을 만듭니다.
「바로쓰는 HTML공지 스킬 만들기」 강의에서 나눠 드린 「IRIS 공지 HTML 작성 규칙 (공유용)」 문서를 skill로 묶은 것입니다.

## 다운로드

[iris-notice-html-skill.zip 받기 (v2)](https://github.com/dkaieduteam/dk-ai-lab/releases/download/iris-notice-html-v2/iris-notice-html-skill.zip)

## 설치 방법

1. `iris-notice-html-skill.zip`을 받습니다. 압축은 풀지 않습니다.
2. 쓰고 있는 AI 서비스(ChatGPT, Claude 등)의 skill 설치 메뉴에 받은 zip 파일을 그대로 올립니다.
3. 설치가 끝나면 skill 목록에 `iris-notice-html`이 보입니다.

skill 메뉴 위치는 서비스마다 다르고 자주 바뀝니다. 찾기 어려우면 쓰는 AI에게 「skill zip 파일 설치하는 방법 알려 줘」라고 물어보면 됩니다.

skill을 쓰지 않는 AI라면 zip 안의 `iris-notice-html/references/IRIS_공지_HTML_작성규칙.md` 문서를 채팅에 붙여넣고 「이 규칙을 지켜서 공지 HTML을 만들어 줘」라고 요청해도 됩니다.

## 준비

- skill 설치를 지원하는 AI 서비스 (ChatGPT, Claude 등)

## 사용법

1. 새 채팅에서 공지 내용을 적어 요청합니다. 예: 「12월 안전교육 참석 안내 공지 만들어 줘. 대상은 생산팀 전원, 일시는 …」. 공지에 넣을 사진·로고가 있으면 함께 올립니다.
2. 빠진 정보가 있으면 AI가 먼저 묻습니다. 답하면 HTML 파일을 만들고 점검 결과를 알려 줍니다.
3. 만든 HTML 파일을 내려받아 메모장으로 열고 전체를 복사합니다. IRIS 글쓰기에서 에디터의 HTML 편집 화면에 붙여넣고, 미리보기를 확인한 뒤 등록합니다.

디자인(색·배치)은 마음대로 바꿔 달라고 하면 됩니다. 규칙 문서는 zip 안의 `iris-notice-html/references/` 폴더에 있습니다.

## 버전 기록

| 버전 | 날짜 | 바뀐 점 |
|---|---|---|
| v2 | 2026-11-23 | 설치용 `.bat` 파일을 빼고 skill 폴더만 zip으로 묶음. 쓰는 AI 서비스에 zip을 그대로 올려 설치하도록 안내를 바꿈 |
| v1 | 2026-11-17 | 처음 게시 |
