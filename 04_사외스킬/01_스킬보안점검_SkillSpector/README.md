# 스킬 보안 점검 (SkillSpector)

> **만든 곳**: NVIDIA · 찾아가는 AI교육서비스팀이 만든 도구가 아닙니다.
> **원본**: <https://github.com/NVIDIA/SkillSpector>
> **라이선스**: Apache License 2.0

> **⚠ 사외 skill을 받기 전에는 이 도구로 먼저 보안 점검을 하시길 권합니다.** [04_사외스킬](..)에 있는 skill도, 인터넷에서 찾은 skill도 설치하기 전에 한 번 검사합니다.

이 저장소에는 파일을 따로 두지 않습니다. 원본 주소에서 바로 설치하면 NVIDIA가 고친 최신 내용을 받을 수 있습니다.

## 어떤 도구인가요

인터넷에서 받은 skill을 설치하기 **전에** 위험한 내용이 들어 있지 않은지 검사하는 도구입니다.

skill은 한 번 설치하면 AI가 그 안의 지시와 스크립트를 별다른 확인 없이 따릅니다. 그래서 공개된 skill 가운데 일부에는 내 파일·계정 정보를 밖으로 보내거나, AI의 안전 규칙을 무시하게 만드는 내용이 숨어 있기도 합니다. NVIDIA가 공개 skill 31,132개를 분석했더니 26.1%에 취약점이 있었고, 5.2%는 악의적인 의도가 보였습니다.

- 만든 목적: 「이 skill, 설치해도 괜찮을까?」에 답하는 것
- 검사하는 것: 프롬프트 인젝션, 정보 유출, 권한 상승, 위험한 코드 실행, 의존 패키지 위험 등 17개 분류 71가지 패턴
- 검사할 수 있는 것: skill 폴더, `SKILL.md` 파일 하나, zip 파일, GitHub 주소
- 결과: 0~100점 위험 점수와 권고

| 점수 | 위험도 | 권고 |
|---|---|---|
| 0~20 | LOW | SAFE (설치해도 됨) |
| 21~50 | MEDIUM | CAUTION (내용을 확인하고 설치) |
| 51~100 | HIGH · CRITICAL | DO NOT INSTALL (설치하지 않음) |

이 저장소의 [03_DK스킬](../../03_DK스킬)처럼 다른 사람이 나눠 준 skill을 받을 때도 먼저 돌려 볼 수 있습니다.

## 설치 방법

두 가지로 구성되어 있습니다. **검사 프로그램**(`skillspector`)과, AI가 그 프로그램을 돌리고 결과를 읽어 주는 **skill**(`skill-inspector`)입니다. 둘 다 설치하면 AI에게 말로 검사를 시킬 수 있습니다.

### 1. 검사 프로그램 설치

Python 3.12 또는 3.13이 필요합니다. ChatGPT 앱(Codex)이나 Claude Code에 아래처럼 부탁하면 대신 설치해 줍니다.

```
https://github.com/NVIDIA/SkillSpector 의 설치 안내대로 skillspector 를 설치해 줘. uv 로 Python 3.13 을 지정해서 설치해.
```

직접 설치하려면 [uv](https://docs.astral.sh/uv/)를 설치한 뒤 아래 명령을 실행합니다.

```
uv tool install --python 3.13 git+https://github.com/NVIDIA/skillspector.git
```

### 2. skill 설치

**ChatGPT 데스크탑 앱**: 새 채팅(Ctrl+N)에 아래 문장을 붙여넣어 보냅니다. 설치 후 새 채팅에서 `$`를 쳐서 목록에 `skill-inspector`가 보이면 됩니다.

```
$skill-installer https://github.com/NVIDIA/SkillSpector/tree/main/skills/skill-inspector 이 skill 설치해 줘
```

**Claude Code**: 원본의 [skills/skill-inspector](https://github.com/NVIDIA/SkillSpector/tree/main/skills/skill-inspector) 폴더를 `C:\Users\<내 계정>\.claude\skills\skill-inspector\`에 넣거나, Claude Code에게 이 주소의 skill을 설치해 달라고 부탁합니다.

## 사용법

1. 검사할 skill 폴더나 zip을 받아 둡니다. **아직 설치하지 않습니다.**
2. AI에게 검사를 부탁합니다. 예:
   ```
   $skill-inspector 다운로드 폴더의 print-design-skill.zip 설치해도 되는지 검사해 줘
   ```
3. AI가 `skillspector`로 검사한 뒤, 걸린 부분의 원문을 직접 읽고 `APPROVE`(설치해도 됨) · `CAUTION`(주의) · `REJECT`(설치하지 않음) 가운데 하나로 알려 줍니다.

명령으로 직접 돌리려면 아래처럼 실행합니다. `--no-llm`은 내 PC 안에서만 검사하는 옵션입니다.

```
skillspector scan ./검사할-skill-폴더/ --no-llm
```

## 주의할 점

- 점수만 보고 판단하지 않습니다. 점수가 낮아도 놓친 위험이 있을 수 있으니, CAUTION 이상이면 걸린 부분을 꼭 읽어 봅니다.
- `--no-llm` 없이 돌리면 검사할 skill 내용을 외부 AI(API)로 보내 추가 분석합니다. 회사 자료가 들어 있는 skill은 `--no-llm`으로만 검사합니다.
- 검사할 skill 안의 스크립트(`.bat`, `.py` 등)는 검사가 끝나기 전에 실행하지 않습니다.

## 기록

| 날짜 | 바뀐 점 |
|---|---|
| 2026-11-17 | 처음 게시 (원본 주소 안내) |
