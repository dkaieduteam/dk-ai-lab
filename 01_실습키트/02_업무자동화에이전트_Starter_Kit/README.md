# 업무자동화 에이전트 Starter_Kit

"업무자동화 에이전트 만들기" 교육(그룹사 특별기본 과정)에서 쓰는 실습 세트입니다. 내 PC의 로컬 MCP 서버와 OpenAI Secure MCP Tunnel을 띄워 ChatGPT가 NAVER WORKS 메일을 조회하고, 주간보고 초안과 메일 App Link를 만드는 흐름을 그대로 재현합니다.

## 다운로드

[starter_kit.zip 받기 (v1)](https://github.com/dkaieduteam/dk-ai-lab/releases/download/ai-agent-v1/starter_kit.zip)

## 받은 뒤 할 일

1. `starter_kit.zip`을 받습니다.
2. 압축을 풀기 전에 zip 파일을 마우스 오른쪽 버튼으로 클릭 → 속성 → 「차단 해제」를 체크하고 확인을 누릅니다.
3. 압축을 풀고 `Starter_kit` 폴더를 엽니다.

2번을 하지 않으면 `.cmd`·`.vbs` 파일을 실행할 때 「Windows의 PC 보호」 경고가 뜹니다.

## 사용 환경

| 항목 | 요구사항 |
|---|---|
| OS | Windows 10/11 (x64) |
| Node.js | 24 LTS 이상 (설치 후 재부팅 1회) |
| ChatGPT | 데스크톱 앱 설치, 커스텀 MCP 플러그인 사용 가능 플랜(Business Standard 등) 로그인 |
| NAVER WORKS | 본인 메일·메신저 로그인 계정 (실습 전용 메일 폴더·접두어 설정 필요) |
| OpenAI Platform | 본인 계정으로 Tunnel·API Key 발급 필수 |

## .env 설정

Starter_kit 루트에 `.env` 파일이 포함돼 있지만 값이 비어 있습니다. 본 스타터키트는 **교육 당일 사용한 교육팀 공용 계정으로는 더 이상 실습이 불가능**하며, **본인 NAVER WORKS 계정과 본인 OpenAI Platform 계정**으로만 실행됩니다. 아래 3가지 값을 사전 발급·입력해야 `START_HERE.cmd` 가 정상 동작합니다.

1. **NAVER WORKS 계정 (`NW_ID`·`NW_PW`)**: 본인 NAVER WORKS 이메일과 비밀번호를 각각 입력합니다.
2. **OpenAI Platform Tunnel (`TUNNEL_ID`)**: [https://platform.openai.com/settings/organization/tunnels](https://platform.openai.com/settings/organization/tunnels) 에서 `Create tunnel`로 생성한 `tunnel_...` 값을 입력합니다 (Organizations = Personal).
3. **OpenAI API Key (`API_KEY`)**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) 에서 `Create new secret key`로 발급(`Restricted` · `Tunnels` 의 `Read` + `Use` 만 허용)해 `sk-...` 값을 입력합니다. 만료 30일 이내 권장.

## 실행 흐름

### 1. 환경 준비·연결 (Chap 1·2)

1. `START_HERE.cmd` 더블클릭. 자동으로 4단계가 진행됩니다 (환경 점검 → `.env` 로드 → MCP 서버 시작 → Tunnel 연결). 1분 안에 `[READY] 실습 준비 완료` 메시지에 도달합니다.
2. ChatGPT 데스크톱 앱에서 `플러그인 → 추가 → 사용자 지정 MCP 서버 추가` → 연결 방식 `터널` → 본인 Tunnel 선택 → 인증 방식 `인증 없음` → `플러그인으로 생성`.
3. 플러그인 목록에서 도구 5개를 확인합니다 (`get_training_profile`·`search_training_mails`·`read_training_mail`·`create_training_mail_applink`·`create_training_message_applink`).

### 2. 메일 조회·보고서 작성 (Chap 3~5)

ChatGPT 대화창에서 교안의 프롬프트를 순서대로 실행합니다. 더미 메일 4건을 근거로 주간보고 초안과 메일 App Link가 자동으로 만들어집니다. 최종 발송은 사람이 NAVER WORKS 임시보관함에서 직접 수행합니다.

### 3. 자동화 2단 (Chap 6·7, 선택)

- **Chap 6 — Windows 작업 스케줄러**: PC 로그온 시 `AI_Scheduler_NAVERWORKS.vbs`가 백그라운드로 Starter_kit을 실행해 `[READY]`까지 자동 도달.
- **Chap 7 — ChatGPT Tasks 예약**: 매주 정해진 시각에 `search_training_mails` + `create_training_mail_applink`가 자동 호출되어 주간보고 초안과 App Link가 Automation 폴더에 저장됩니다.

## 종료

실습이 끝나면 `STOP_HERE.cmd`를 더블클릭합니다. MCP·Tunnel 프로세스가 종료되고 포트 해제까지 검증된 뒤 cleanup이 완료됩니다. 본인 계정 사용자는 OpenAI Platform에서 API Key `Revoke`를 함께 수행합니다.

## 폴더 구조

```
Starter_kit/
├─ START_HERE.cmd                자동 실행 진입점 (환경 점검·MCP·Tunnel → [READY])
├─ STOP_HERE.cmd                 종료·회수 (포트 해제 검증 포함)
├─ AI_Scheduler_NAVERWORKS.vbs   Windows 작업 스케줄러 등록용 (Chap 6)
├─ .env                          설정 파일 (값 공란 — 위 안내대로 입력)
├─ VERSION.txt                   버전·호환 정보
├─ manifest.sha256               파일 무결성 해시
├─ naverworks-mail-mcp/          로컬 MCP 서버 (Node.js)
├─ scripts/                      PowerShell 유틸 스크립트
├─ tunnel-client-v0.0.15/        OpenAI Tunnel 클라이언트
├─ SampleData/                   가상 지점 매출 xlsx 4개 (Chap 3 실습용)
└─ logs/                         실행 로그 저장 (자동 생성 · 자격증명 자동 마스킹)
```

## 문의

궁금하신 점은 IRIS 게시판 「[찾아서] AI 무엇이든 물어보세요」(IRIS → 동국시스템즈 → [찾아서])에 남겨 주시기 바랍니다. 질문과 답변이 함께 쌓여 다른 분들께도 도움이 됩니다.

## 버전 기록

| 버전 | 날짜 | 바뀐 점 |
|---|---|---|
| v1 | 2026-11-13 | 처음 게시. Chap 1·2 재편 (.env 리뷰 선두), Chap 7 GPT Tasks 예약 자동화 추가, STOP_HERE 포트 폴링 안정화 반영. |
