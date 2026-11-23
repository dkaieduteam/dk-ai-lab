# 인쇄물 제작 skill (print-design)

현수막·세로배너·족자·포스터·초청장·감사장·전단 같은 인쇄물 시안을 만들고, 인쇄소에 넘길 CMYK PDF로 저장하는 skill입니다.
종이 인쇄물은 화면 공유용 PNG·JPG도 함께 만듭니다.
강의에서 직접 다룬 skill은 아닙니다. 「바로쓰는 HTML공지 스킬 만들기」 강의 뒤에 수강생 질문을 받고, 문의 대응으로 만든 skill입니다.

## 다운로드

[print-design-skill.zip 받기 (v2)](https://github.com/dkaieduteam/dk-ai-lab/releases/download/print-design-v2/print-design-skill.zip)

## 설치 방법

1. `print-design-skill.zip`을 받습니다. 압축은 풀지 않습니다.
2. 쓰고 있는 AI 서비스(ChatGPT, Claude 등)의 skill 설치 메뉴에 받은 zip 파일을 그대로 올립니다.
3. 설치가 끝나면 skill 목록에 `print-design`이 보입니다.

skill 메뉴 위치는 서비스마다 다르고 자주 바뀝니다. 찾기 어려우면 쓰는 AI에게 「skill zip 파일 설치하는 방법 알려 줘」라고 물어보면 됩니다.

## 준비

- skill 설치를 지원하는 AI 서비스 (ChatGPT, Claude 등)
- 코드 실행 기능 (Python으로 PDF 조립·글꼴 받기·그래픽 변환을 합니다)

AI가 라이브러리가 없다고 하면 아래 목록을 설치해 달라고 요청합니다.

```
pip install reportlab pymupdf pillow fonttools numpy brotli scikit-image
```

## 사용법

1. 새 채팅에서 만들 인쇄물을 요청합니다. 예: 「행사 현수막 만들어 줘」, 「초청장 시안」. 로고 원본이나 레퍼런스 이미지가 있으면 함께 올립니다.
2. 처음 쓰면 저작권·인쇄·정보 보호 안내가 먼저 나옵니다. 읽고 넘어갑니다.
3. AI가 품목·크기·문구를 묻습니다. 답하면 글꼴(눈누 무료 글꼴)과 배경을 정해 시안을 만듭니다.
4. 결과 PDF는 초안입니다. 발주할 인쇄소의 작업 규격과 교정본 색을 확인한 뒤 최종본으로 씁니다.

인쇄 규격·글꼴·저작권 기준은 zip 안의 `print-design/references/` 폴더에 있습니다. 우리 기준과 다르면 압축을 풀어 이 파일을 고치고, `print-design` 폴더를 다시 zip으로 묶어 설치합니다.

## 버전 기록

| 버전 | 날짜 | 바뀐 점 |
|---|---|---|
| v2 | 2026-11-23 | 설치용 `.bat` 파일을 빼고 skill 폴더만 zip으로 묶음. 쓰는 AI 서비스에 zip을 그대로 올려 설치하도록 안내를 바꿈 |
| v1 | 2026-11-16 | 처음 게시 |
