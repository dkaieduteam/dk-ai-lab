# IRIS 공지 HTML skill (iris-notice-html)

IRIS 게시판에 붙여넣을 HTML 공지를 만드는 skill입니다.
IRIS 에디터는 붙여넣은 HTML의 앞부분을 미리보기로 긁어 가고, 여백·행간·제목 서식을 강제로 바꿉니다. 이 skill은 「IRIS 공지 HTML 작성 규칙」을 지켜서 미리보기에는 한글 요약이 잡히고 디자인은 깨지지 않는 HTML을 만듭니다.
「바로쓰는 HTML공지 스킬 만들기」 강의에서 나눠 드린 「IRIS 공지 HTML 작성 규칙 (공유용)」 문서를 skill로 묶은 것입니다.

## 다운로드

[iris-notice-html-skill.zip 받기 (v1)](https://github.com/dkaieduteam/dk-ai-lab/releases/download/iris-notice-html-v1/iris-notice-html-skill.zip)

## 받은 뒤 할 일

1. `iris-notice-html-skill.zip`을 받습니다.
2. 압축을 풀기 전에 zip 파일을 마우스 오른쪽 버튼으로 클릭 → 속성 → 「차단 해제」를 체크하고 확인을 누릅니다.
3. 압축을 풀고 `IRIS공지HTML_skill` 폴더를 엽니다.

2번을 하지 않으면 `.bat` 파일을 실행할 때 「Windows의 PC 보호」 경고가 뜹니다.

## 준비

- ChatGPT 데스크탑 앱

## 등록 방법

1. `skill 설치.bat`을 더블클릭합니다. `iris-notice-html` skill이 이 PC의 Codex skills 폴더에 설치됩니다.
2. ChatGPT 앱에서 새 채팅(Ctrl+N)을 열고 입력창에 `$`를 치면 목록에 `Iris Notice Html`이 보입니다.
3. 지우려면 `skill 지우기.bat`을 실행합니다.

Claude를 쓰면 `iris-notice-html` 폴더를 zip으로 묶어 Claude 앱의 Skills 메뉴에서 올리거나, Claude Code의 `.claude/skills/` 폴더에 넣습니다.
skill을 쓰지 않는 AI라면 `iris-notice-html/references/IRIS_공지_HTML_작성규칙.md` 문서를 채팅에 붙여넣고 「이 규칙을 지켜서 공지 HTML을 만들어 줘」라고 요청해도 됩니다.

## 사용법

1. 결과 파일을 저장할 폴더를 하나 만들고, 공지에 넣을 사진·로고가 있으면 함께 넣습니다.
2. ChatGPT 앱에서 그 폴더를 엽니다. 「파일」 → 「폴더 열기」로 고르고 「폴더 신뢰」를 누릅니다.
3. 새 채팅에서 `$`로 `Iris Notice Html`을 고르고 공지 내용을 적어 요청합니다. 예: 「12월 안전교육 참석 안내 공지 만들어 줘. 대상은 생산팀 전원, 일시는 …」.
4. 빠진 정보가 있으면 AI가 먼저 묻습니다. 답하면 HTML 파일을 만들고 점검 결과를 알려 줍니다.
5. 만든 HTML 파일을 메모장으로 열어 전체를 복사합니다. IRIS 글쓰기에서 에디터의 HTML 편집 화면에 붙여넣고, 미리보기를 확인한 뒤 등록합니다.

디자인(색·배치)은 마음대로 바꿔 달라고 하면 됩니다. 규칙 문서는 `iris-notice-html/references/` 폴더에 있습니다.

## 버전 기록

| 버전 | 날짜 | 바뀐 점 |
|---|---|---|
| v1 | 2026-11-17 | 처음 게시 |
