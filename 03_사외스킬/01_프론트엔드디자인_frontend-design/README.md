# 프론트엔드 디자인 skill (frontend-design)

> **만든 곳**: Anthropic (Claude를 만든 회사) · 찾아가는 AI교육서비스팀이 만든 skill이 아닙니다.
> **원본**: <https://github.com/anthropics/skills/tree/main/skills/frontend-design>
> **라이선스**: Apache License 2.0 (원본 폴더의 `LICENSE.txt`)

이 저장소에는 skill 파일을 따로 두지 않습니다. 원본 주소에서 바로 설치하면 Anthropic이 고친 최신 내용을 받을 수 있습니다.

## 어떤 skill인가요

AI에게 웹 화면이나 HTML을 만들어 달라고 하면 흔히 비슷한 모양(보라색 그라데이션, 큰 숫자 카드, 둥근 박스 나열)이 나옵니다. 이 skill은 AI가 그런 기본 틀을 피하고, 만들 화면의 주제·보는 사람·목적에 맞춰 분위기·글꼴·색·배치를 먼저 정한 뒤 디자인하게 합니다.

- 만든 목적: 「템플릿으로 찍어 낸 것 같은」 화면 대신, 주제가 드러나는 디자인을 만들게 하는 것
- 잘 맞는 일: 사내 공지·안내 HTML, 행사·교육 소개 페이지, 랜딩 페이지, 간단한 화면 시안
- 강의에서: 「바로쓰는 HTML공지 스킬 만들기」에서 HTML 공지 디자인을 다듬을 때 함께 썼습니다.

## 설치 방법

### ChatGPT 데스크탑 앱

1. 새 채팅(Ctrl+N)을 열고 아래 문장을 그대로 붙여넣어 보냅니다.
   ```
   $skill-installer https://github.com/anthropics/skills/tree/main/skills/frontend-design 이 skill 설치해 줘
   ```
2. 설치가 끝나면 새 채팅을 다시 열고 입력창에 `$`를 칩니다. 목록에 `frontend-design`이 보이면 됩니다.

설치가 안 되면 원본 주소를 열어 `SKILL.md`와 `LICENSE.txt`를 받아 `frontend-design` 폴더에 넣고, 그 폴더를 `C:\Users\<내 계정>\.codex\skills\` 안에 복사합니다.

### Claude (앱 · Claude Code)

따로 받지 않아도 됩니다. Anthropic 공식 skill이라 Claude 앱과 Claude Code에서 바로 켜서 쓸 수 있습니다.

## 사용법

1. 결과 파일을 저장할 폴더를 ChatGPT 앱에서 엽니다. 「파일」 → 「폴더 열기」로 고르고 「폴더 신뢰」를 누릅니다.
2. 새 채팅에서 `$`로 `frontend-design`을 고르고 만들 화면을 요청합니다. 예: 「사내 공지용 HTML 페이지 만들어 줘」.
3. AI가 디자인 방향을 정해 HTML을 만듭니다. 마음에 들지 않으면 분위기나 색을 바꿔 달라고 다시 요청합니다.

## 기록

| 날짜 | 바뀐 점 |
|---|---|
| 2026-11-17 | zip 배포를 그만두고 원본 주소에서 바로 설치하는 안내로 바꿈 |
| 2026-11-16 | 처음 게시 (원본 사본 + 설치 파일 zip) |
