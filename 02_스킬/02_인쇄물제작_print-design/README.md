# 인쇄물 제작 skill (print-design)

현수막·세로배너·족자·포스터·초청장·감사장·전단 같은 인쇄물 시안을 만들고, 인쇄소에 넘길 CMYK PDF로 저장하는 skill입니다.
종이 인쇄물은 화면 공유용 PNG·JPG도 함께 만듭니다.
「바로쓰는 HTML공지 스킬 만들기」 강의에서 다룬 skill과 같은 것입니다.

## 다운로드

[print-design-skill.zip 받기 (v1)](https://github.com/dkaieduteam/dk-ai-lab/releases/download/print-design-v1/print-design-skill.zip)

## 받은 뒤 할 일

1. `print-design-skill.zip`을 받습니다.
2. 압축을 풀기 전에 zip 파일을 마우스 오른쪽 버튼으로 클릭 → 속성 → 「차단 해제」를 체크하고 확인을 누릅니다.
3. 압축을 풀고 `인쇄물제작_skill` 폴더를 엽니다.

2번을 하지 않으면 `.bat` 파일을 실행할 때 「Windows의 PC 보호」 경고가 뜹니다.

## 준비

- ChatGPT 데스크탑 앱
- Python과 아래 라이브러리 (PDF 조립·글꼴 받기·그래픽 변환에 씁니다)

```
pip install reportlab pymupdf pillow fonttools numpy brotli scikit-image
```

## 등록 방법

1. `skill 설치.bat`을 더블클릭합니다. `print-design` skill이 이 PC의 Codex skills 폴더에 설치됩니다.
2. ChatGPT 앱에서 새 채팅(Ctrl+N)을 열고 입력창에 `$`를 치면 목록에 `Print Design`이 보입니다.
3. 지우려면 `skill 지우기.bat`을 실행합니다.

## 사용법

1. 결과 파일을 저장할 폴더를 하나 만들고, 로고 원본이나 레퍼런스 이미지가 있으면 함께 넣습니다.
2. ChatGPT 앱에서 그 폴더를 엽니다. 「파일」 → 「폴더 열기」로 고르고 「폴더 신뢰」를 누릅니다.
3. 새 채팅에서 `$`로 `Print Design`을 고르고 만들 인쇄물을 요청합니다. 예: 「행사 현수막 만들어 줘」, 「초청장 시안」.
4. 처음 쓰면 저작권·인쇄·정보 보호 안내가 먼저 나옵니다. 읽고 넘어갑니다.
5. AI가 품목·크기·문구를 묻습니다. 답하면 글꼴(눈누 무료 글꼴)과 배경을 정해 시안을 만듭니다.
6. 결과 PDF는 초안입니다. 발주할 인쇄소의 작업 규격과 교정본 색을 확인한 뒤 최종본으로 씁니다.

인쇄 규격·글꼴·저작권 기준은 `print-design/references/` 폴더에 있습니다. 우리 기준과 다르면 이 파일을 고친 뒤 `skill 설치.bat`을 다시 실행합니다.

## 버전 기록

| 버전 | 날짜 | 바뀐 점 |
|---|---|---|
| v1 | 2026-11-16 | 처음 게시 |
