# 출장복명 skill (trip-report)

영수증 사진으로 출장 복명·당일 외근 복명 엑셀과 전자결재용 기타보고를 만드는 skill입니다.
재경실 워크샵에서 완성한 skill과 같은 것입니다.

## 다운로드

[trip-report-skill.zip 받기 (v2)](https://github.com/dkaieduteam/dk-ai-lab/releases/download/trip-report-v2/trip-report-skill.zip)

## 설치 방법

1. `trip-report-skill.zip`을 받습니다. 압축은 풀지 않습니다.
2. 쓰고 있는 AI 서비스(ChatGPT, Claude 등)의 skill 설치 메뉴에 받은 zip 파일을 그대로 올립니다.
3. 설치가 끝나면 skill 목록에 `trip-report`가 보입니다.

skill 메뉴 위치는 서비스마다 다르고 자주 바뀝니다. 찾기 어려우면 쓰는 AI에게 「skill zip 파일 설치하는 방법 알려 줘」라고 물어보면 됩니다.

## 준비

- skill 설치를 지원하는 AI 서비스 (ChatGPT, Claude 등)
- 코드 실행 기능 (Python으로 회사 양식 엑셀을 채우고 영수증 이미지를 붙입니다)

## 사용법

1. 새 채팅에 영수증 사진을 올립니다. 1박 이상이면 숙박 예약 내역과 매출전표도 함께 올립니다.
2. 「출장복명 만들어 줘」라고 요청합니다. AI가 `trip-report` skill을 불러 작업합니다.
3. AI가 영수증에서 읽은 날짜·구간·금액을 표로 보여 줍니다. 맞는지 확인하고, 묻는 값(부서·이름·출장 목적 등)에 답합니다.
4. 확인이 끝나면 회사 양식 엑셀이 만들어집니다. 1박 이상은 출장 복명, 당일은 외근 복명입니다. 만든 파일을 내려받아 씁니다.

정산 기준은 zip 안의 `trip-report/출장정산_규칙.md`에 있습니다. 우리 회사 기준과 다르면 압축을 풀어 이 파일을 고치고, `trip-report` 폴더를 다시 zip으로 묶어 설치합니다.

## 버전 기록

| 버전 | 날짜 | 바뀐 점 |
|---|---|---|
| v2 | 2026-11-23 | 설치용 `.bat` 파일을 빼고 skill 폴더만 zip으로 묶음. 쓰는 AI 서비스에 zip을 그대로 올려 설치하도록 안내를 바꿈 |
| v1 | 2026-11-16 | 처음 게시 |
