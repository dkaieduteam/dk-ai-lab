---
version: alpha
name: Monochrome Yellow Pop
description: 카카오 기업 사이트(kakaocorp.com/page) 메인·서브 8개 화면의 실측 스타일과 사이트 자체 다크 모드 스타일 값을 합쳐 뽑은 **다크 모드 기준** 참고용 디자인 기준. 검정 바탕·흰 글자의 무채색 위계 위에 노랑 한 가지만 행동 색으로 쓰고, 아주 큰 굵은 제목·넉넉한 여백·완전히 둥근 알약형 버튼으로 구성한다. 해당 회사의 공식 디자인 시스템이 아니다.
colors:
  primary: "#FFFFFF"
  secondary: "#A8A8A8"
  tertiary: "#FAE100"
  neutral: "#000000"
  background: "#000000"
  foreground: "#FFFFFF"
  text-strong: "#F3F3F3"
  text-body: "#D4D4D4"
  text-secondary: "#A8A8A8"
  text-tertiary: "#888888"
  text-muted: "#666666"
  surface: "#333333"
  surface-subtle: "#111111"
  chip: "#4A4A4A"
  border: "#333333"
  border-strong: "#F3F3F3"
  inverse-background: "#FFFFFF"
  inverse-foreground: "#000000"
  accent-yellow: "#FAE100"
  on-accent: "#000000"
  link: "#489FF8"
  accent-pink: "#F73C99"
  accent-blue: "#2D82FF"
  accent-violet: "#7357FF"
  accent-orange: "#FF9D00"
  error: "#FF4D5A"
  error-surface: "#3A1418"
typography:
  display-xl:
    fontFamily: Apple SD Gothic Neo
    fontSize: 80px
    fontWeight: 700
    lineHeight: 100px
    letterSpacing: -2px
  display-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 60px
    fontWeight: 700
    lineHeight: 70px
    letterSpacing: -2px
  headline-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 48px
    fontWeight: 700
    lineHeight: 60px
    letterSpacing: -1.2px
  headline-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 36px
    fontWeight: 700
    lineHeight: 52px
    letterSpacing: -0.8px
  headline-sm:
    fontFamily: Apple SD Gothic Neo
    fontSize: 32px
    fontWeight: 700
    lineHeight: 44px
    letterSpacing: -0.8px
  title-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 26px
    fontWeight: 700
    lineHeight: 36px
    letterSpacing: -0.6px
  title-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 22px
    fontWeight: 700
    lineHeight: 32px
    letterSpacing: -0.6px
  title-sm:
    fontFamily: Apple SD Gothic Neo
    fontSize: 20px
    fontWeight: 700
    lineHeight: 30px
    letterSpacing: -0.5px
  body-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 17px
    fontWeight: 400
    lineHeight: 27px
    letterSpacing: -0.5px
  body-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 16px
    fontWeight: 400
    lineHeight: 28px
    letterSpacing: -0.5px
  label-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 14px
    fontWeight: 400
    lineHeight: 22px
    letterSpacing: -0.25px
  label-sm:
    fontFamily: Apple SD Gothic Neo
    fontSize: 13px
    fontWeight: 700
    lineHeight: 17px
    letterSpacing: 0px
  caption:
    fontFamily: Apple SD Gothic Neo
    fontSize: 12px
    fontWeight: 400
    lineHeight: 18px
    letterSpacing: 0px
rounded:
  sm: 8px
  md: 16px
  lg: 20px
  xl: 24px
  pill: 999px
  full: 9999px
spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 60px
  section: 120px
  section-end: 200px
  gutter-mobile: 20px
  gutter-tablet: 40px
  gutter-desktop: 72px
  container: 1296px
  header-height: 72px
  header-height-mobile: 58px
components:
  header:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.body-lg}"
    height: 72px
  nav-item:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.body-lg}"
    rounded: "{rounded.pill}"
    padding: 4px 16px 6px
    height: 37px
  nav-item-active:
    backgroundColor: "{colors.inverse-background}"
    textColor: "{colors.inverse-foreground}"
  button-primary:
    backgroundColor: "{colors.inverse-background}"
    textColor: "{colors.inverse-foreground}"
    typography: "{typography.body-lg}"
    rounded: "{rounded.xl}"
    padding: 0 22px
    height: 48px
  button-accent:
    backgroundColor: "{colors.accent-yellow}"
    textColor: "{colors.on-accent}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.md}"
    padding: 7px 13px 8px
    height: 32px
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text-strong}"
    typography: "{typography.caption}"
    rounded: "{rounded.lg}"
    padding: 9px 10px 10px 16px
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    typography: "{typography.caption}"
    rounded: "{rounded.xl}"
    padding: 10px 20px 12px
    height: 40px
  tab:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.body-lg}"
    rounded: "{rounded.pill}"
    padding: 12px 24px
  tab-active:
    backgroundColor: "{colors.inverse-background}"
    textColor: "{colors.inverse-foreground}"
  tag:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.label-md}"
    rounded: "{rounded.sm}"
    padding: 6px 12px
  hashtag:
    textColor: "{colors.text-secondary}"
    typography: "{typography.label-md}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.xl}"
    padding: 32px
  card-title:
    textColor: "{colors.foreground}"
    typography: "{typography.title-lg}"
  icon-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.full}"
    size: 48px
  icon-button-small:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-strong}"
    rounded: "{rounded.full}"
    size: 32px
  list-row:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text-strong}"
    typography: "{typography.body-md}"
    height: 65px
  hero-band:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.foreground}"
    typography: "{typography.headline-lg}"
    padding: 100px 0
  hero-dark:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.display-xl}"
  search-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    typography: "{typography.body-lg}"
    rounded: "{rounded.xl}"
    padding: 20px 24px 20px 56px
  link-inline:
    textColor: "{colors.link}"
  page:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.text-body}"
    typography: "{typography.body-md}"
  date-label:
    textColor: "{colors.text-tertiary}"
    typography: "{typography.label-md}"
  card-caption:
    textColor: "{colors.text-secondary}"
    typography: "{typography.caption}"
  divider:
    backgroundColor: "{colors.border}"
    height: 1px
  divider-strong:
    backgroundColor: "{colors.border-strong}"
    height: 1px
  category-fill-pink:
    backgroundColor: "{colors.accent-pink}"
    rounded: "{rounded.sm}"
  category-fill-blue:
    backgroundColor: "{colors.accent-blue}"
    rounded: "{rounded.sm}"
  category-fill-violet:
    backgroundColor: "{colors.accent-violet}"
    rounded: "{rounded.sm}"
  category-fill-orange:
    backgroundColor: "{colors.accent-orange}"
    rounded: "{rounded.sm}"
  input-error:
    backgroundColor: "{colors.error-surface}"
    textColor: "{colors.text-strong}"
    typography: "{typography.label-md}"
  input-error-border:
    backgroundColor: "{colors.error}"
    height: 1px
---

# Design System: Monochrome Yellow Pop (다크 모드 기준)

> **출처·성격**: 카카오 기업 사이트 [kakaocorp.com/page](https://www.kakaocorp.com/page/)의 메인과 서브 7개 화면(전체 서비스·서비스 상세·문화·보도자료·카카오이야기·AI·지속가능성)을 2026-10-23에 PC(1440px)·모바일(390px)로 열어 **계산된 스타일 값을 직접 재서** 정리한 참고 기준이다. **해당 회사의 공식 디자인 시스템이 아니다.** 로고·캐릭터·서비스 아이콘·사진·문구는 넣지 않았고, 색·글자 크기·여백·모서리 같은 **수치와 규칙만** 옮겼다.
>
> **다크 기준 (2026-10-30 개정)**: 이 파일의 기본값은 **다크 모드**다. 사이트는 헤더의 화면 모드 버튼으로 다크 모드를 제공하며, 다크 값은 ① 2026-10-23 실측(바탕 `#000`·카드 `#333`·보조 글자 `#A8A8A8`)과 ② 2026-10-30 사이트 공개 스타일시트(`.dark` 규칙)에서 확인한 값(본문 `#A8A8A8`·굵은 글자 `#F3F3F3`·링크 `#489FF8`·눌림 면 `#4A4A4A`·비활성 `#666`·흰 면+검정 아이콘 반전)을 합쳤다. 사이트에서 직접 확인하지 못해 라이트 규칙을 뒤집어 정한 값은 표에 **「파생」**으로 표시했다. 라이트 모드 원본 값은 맨 아래 「라이트 원본 대조표」에 남겼다.

## Overview

밤의 흑백 포스터처럼 **검정 바탕 위에 노랑 한 점**이 튀는 화면이다. 화면 대부분은 검정 바탕(`#000000`)과 흰 글자(`#FFFFFF`)이고, 회색 단계(`#F3F3F3`→`#D4D4D4`→`#A8A8A8`→`#888`→`#666`)로 정보의 중요도를 가른다. 노랑(`#FAE100`)은 「지금 눌러 볼 것」에만 쓴다 — 어두운 바탕에서는 노랑이 라이트 때보다 더 강하게 튀어서, 눈이 곧장 거기로 간다.

인상을 만드는 요소는 세 가지다(라이트와 같다).

1. **크고 굵고 촘촘한 제목** — 제목은 본문의 3~5배 크기, 굵기 700, 자간을 음수(-0.5 ~ -2px)로 좁혀 한 덩어리로 읽히게 한다.
2. **넉넉한 여백** — 섹션 사이 120px, 페이지 끝 200px. 요소를 채우기보다 비워서 위계를 만든다.
3. **완전히 둥근 형태** — 메뉴·탭·버튼은 알약형(999px), 카드는 24px. 각진 모서리는 거의 없다.

장식(그림자·그라데이션·테두리 상자)은 거의 쓰지 않는다. 구분은 **면 색 차이(검정 ↔ `#333`)와 얇은 선(1px)**으로만 한다. 라이트의 「검정 면 + 흰 글자 반전」은 다크에서 **「흰 면 + 검정 글자 반전」**으로 뒤집힌다.

## Colors

### 무채색 위계 — 화면의 90%

| 토큰 | 값 | 근거 | 쓰임 | 이유 |
|---|---|---|---|---|
| `background` / `neutral` | `#000000` | 실측 | 공지 전체 바탕 | 순검정 — 노랑·흰 글자가 가장 강하게 선다 |
| `foreground` | `#FFFFFF` | 실측 | 제목·메뉴·주요 글자 | 최대 대비 |
| `text-strong` | `#F3F3F3` | 스타일시트(굵은 글자) | 카드 제목·목록 항목·본문 속 굵은 글자 | 흰색보다 한 톤 부드럽게 — 큰 면적에서 덜 눈부시다 |
| `text-body` | `#D4D4D4` | 파생 | 공지 본문 문단 | 사이트 기사 본문은 `#A8A8A8`이지만, 공지는 짧고 꼭 읽혀야 해서 한 단계 밝게 올렸다 |
| `text-secondary` | `#A8A8A8` | 실측·스타일시트 | 설명문·비활성 탭 글자·카드 하단 설명 | 사이트 다크 모드의 기본 보조 글자 색 |
| `text-tertiary` | `#888888` | 파생 | 날짜·해시태그·보조 정보 | 검정 바탕 대비 약 5.9:1 |
| `text-muted` | `#666666` | 스타일시트(비활성) | 비활성 버튼 아이콘·표 안 작은 글자 | 최저 위계. 대비 약 3.7:1이라 **꼭 읽어야 할 글자에는 쓰지 않는다** |
| `surface` | `#333333` | 실측 | 카드·탭·아이콘 버튼·보조 버튼 면 | 사이트 다크 모드의 카드·버튼 면 색 |
| `surface-subtle` | `#111111` | 파생 | 상단 히어로 띠·넓은 구역 | 카드보다 한 단계 어둡게 — 넓은 면적용 |
| `chip` | `#4A4A4A` | 스타일시트(눌림 면) | 눌림·선택 면, `#333` 카드 위 작은 칩 | 카드 위에서 한 단 떠 보인다 |
| `border` | `#333333` | 파생 | 목록 구분선 | |
| `border-strong` | `#F3F3F3` | 파생 | 목록 머리 굵은 선·외곽선 버튼 | 섹션 시작을 밝은 선 하나로 표시 |

### 행동 색 — 한 가지만

| 토큰 | 값 | 쓰임 | 이유 |
|---|---|---|---|
| `accent-yellow` | `#FAE100` | 가장 중요한 행동 1개(다운로드·신청) | 화면당 1~2곳에만 쓴다. 다크에서는 더 강하게 튀므로 **라이트보다 더 아껴 쓴다** |
| `on-accent` | `#000000` | 노랑 위 글자 | 노랑 위 흰 글자는 대비가 부족하다. 다크에서도 반드시 검정 |
| `link` | `#489FF8` | 본문 안 링크 | 사이트 다크 모드 링크 색(스타일시트). 라이트 `#104ADF`는 검정 위에서 보이지 않는다 |

### 보조 강조 색 — 분류 표시에만

`accent-pink #F73C99` · `accent-blue #2D82FF` · `accent-violet #7357FF` · `accent-orange #FF9D00` — 라이트와 같은 값을 쓴다. 카테고리 라벨·일러스트 면 등 **작은 면적**에만 쓴다. 버튼이나 본문 글자 색으로 쓰지 않는다.

### 상태 색 (파생)

`error #FF4D5A`(입력 오류 테두리·아이콘) · `error-surface #3A1418`(오류 안내 바탕). 라이트 `#FF0919`는 검정 위에서 너무 어둡고 탁해 한 단계 밝혔다. 오류 안내 **문구**는 `#F3F3F3` 글자로 쓴다.

### 밝은 면 (반전)

`inverse-background #FFFFFF` · `inverse-foreground #000000` — 다크에서 「가장 앞에 와야 할 것」(현재 메뉴·선택된 탭·주 버튼)은 **흰 면에 검정 글자**로 뒤집는다. 사이트 다크 모드의 버튼 강조 상태(흰 면·검정 아이콘)와 같다. 로고처럼 검정으로 그려진 그림은 색을 뒤집어(흰색으로) 쓴다.

## Typography

원본 사이트는 자체 제작 한글 서체(제목용·본문용 2종, 굵기 400·700)를 쓴다. **이 파일은 그 서체를 쓰지 않는다** — 대신 운영체제 기본 고딕(`"Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif`)으로 같은 크기·굵기·자간을 맞춘다. 원본도 같은 순서로 대체 글꼴을 지정해 두었다.

### 단계 (PC → 모바일)

| 토큰 | PC | 모바일 | 쓰임 |
|---|---|---|---|
| `display-xl` | 80 / 100, 700, -2px | 35 / 46 | 첫 화면 큰 문구 |
| `display-lg` | 60 / 70, 700, -2px | 30 / 40 | 섹션 대표 제목 |
| `headline-lg` | 48 / 60, 700, -1.2px | 30 / 40 | 서브 화면 제목(「전체 서비스」 등) |
| `headline-md` | 36 / 52, 700, -0.8px | 26 / 34 | 섹션 제목(「최신 게시글」) |
| `headline-sm` | 32 / 44, 700, -0.8px | 24 / 34 | 대표 기사 제목 |
| `title-lg` | 26 / 36, 700, -0.6px | 20 / 29 | 카드 제목 |
| `title-md` | 22 / 32, 700, -0.6px | 18 / 28 | 목록 기사 제목 |
| `title-sm` | 20 / 30, 700, -0.5px | 18 / 28 | 소제목·묶음 이름 |
| `body-lg` | 17 / 27, 400, -0.5px | 15 / 24 | 메뉴·탭·버튼 |
| `body-md` | 16 / 28, 400, -0.5px | 16 / 28 | 본문(가장 많이 쓰임) |
| `label-md` | 14 / 22, 400 | 14 / 22 | 해시태그·작은 버튼 |
| `label-sm` | 13 / 17, 700 | 13 / 17 | 노랑 버튼·작은 칩 |
| `caption` | 12 / 18, 400 | 12 / 18 | 바닥글·보조 버튼 |

### 규칙

- **굵기는 400과 700 두 개만.** 중간 굵기를 섞지 않는다 — 대비가 흐려진다.
- **크면 클수록 자간을 더 좁힌다.** 본문 -0.5px, 제목 -0.8 ~ -1.2px, 대형 문구 -2px. 큰 한글은 기본 자간이면 글자가 흩어져 보인다.
- **본문 줄 간격은 1.75배(16/28).** 제목은 1.25 ~ 1.4배로 좁게. 검정 바탕의 흰 글자는 번져 보이므로 본문 줄 간격을 줄이지 않는다.
- **제목과 본문의 크기·밝기 차이를 크게 둔다.** 섹션 제목 36px `#FFFFFF` 아래 본문 16px `#D4D4D4` — 크기 두 배, 밝기 한 단계 차이가 나야 위계가 한눈에 보인다.
- 날짜는 `text-tertiary`(`#888`) 14 ~ 16px로 제목 **위에** 둔다.

## Layout

### 반응형 기준

| 구간 | 너비 | 좌우 여백 |
|---|---|---|
| 데스크톱 | 1440px 이상 | 72px (본문 최대 1296px) |
| 노트북 | 1024 ~ 1439px | 40 ~ 72px |
| 태블릿 | 768 ~ 1023px | 40px |
| 모바일 | 767px 이하 (411px 이하 추가 조정) | 20px |

### 그리드·여백

- **본문 폭 1296px 고정, 가운데 정렬.** 아주 넓은 화면에서도 글줄이 길어지지 않게 한다.
- **좌우 비대칭 2단**: 서브 화면은 왼쪽에 큰 제목(약 45%), 오른쪽에 목록(약 55%)을 둔다. 제목이 「표지」, 목록이 「본문」 역할.
- **카드 3열**, 카드 사이 36px. 모바일은 1열.
- 섹션 사이 **120px**, 페이지 마지막 **200px**, 제목과 내용 사이 40px.
- 헤더 높이 72px(모바일 58px). 메뉴는 가운데, 검색·언어·화면 모드 아이콘은 오른쪽.

### 다크 바탕을 공지에 까는 법

- **바탕색은 공지 맨 바깥 상자에 직접 칠한다**(`background:#000000` + 글자 `color:#D4D4D4`). IRIS·메일은 게시판 자체가 흰 바탕이라, 바깥 상자에 색을 주지 않으면 흰 바탕 위에 흰 글자가 남는다.
- 사용자 기기 설정에 따라 바뀌는 방식(`prefers-color-scheme`)은 쓰지 않는다 — 이 공지는 **항상 다크**로 보인다.
- 바깥 상자 모서리는 `xl`(24px)로 둥글려, 흰 게시판 위에 검정 카드 한 장이 놓인 모양으로 만든다.

## Elevation & Depth

**그림자를 쓰지 않는다.** 실측한 8개 화면 어디에도 카드·버튼 그림자가 없고, 검정 바탕에서는 그림자가 보이지도 않는다. 깊이는 다음 두 가지로만 만든다.

1. **면 밝기 단계** — 검정 바탕(`#000`) 위에 회색 면(`#333`)을 올리면 그것이 「한 단 올라온 것」이다. 그 위에 한 단 더 올릴 것은 `#4A4A4A`.
2. **명암 반전** — 가장 앞에 와야 할 것(현재 메뉴·선택된 탭·주 버튼)은 흰 면에 검정 글자로 뒤집는다.

사이트는 큰 장식 면에만 `#2F2F2F → #0F0F0F` 원형 그라데이션을 쓴다. 공지에는 옮기지 않는다.

## Shapes

| 토큰 | 값 | 쓰임 |
|---|---|---|
| `sm` | 8px | 작은 라벨 칩 |
| `md` | 16px | 작은 버튼(높이 32px) |
| `lg` | 20px | 외곽선 버튼·중간 카드 (실측 최다) |
| `xl` | 24px | 카드·큰 버튼(높이 48px)·검색창·공지 바깥 상자 |
| `pill` | 999px | 메뉴·탭 — 양 끝이 완전한 반원 |
| `full` | 50% | 원형 아이콘 버튼(32·48px) |

**규칙**: 버튼 모서리는 **높이의 절반**이다(높이 32 → 16px, 48 → 24px). 그래서 모든 버튼이 알약 모양이 된다. 사진은 카드 안에서 카드 모서리를 따라 잘린다.

## Components

- **헤더** — 검정 바탕 72px. 메뉴 글자 17px 흰색. 현재 위치 메뉴만 **흰 알약**(검정 글자, 높이 37px, 좌우 16px)으로 뒤집는다. 밑줄·색 글자로 표시하지 않는다.
- **주 버튼** — 흰 바탕·검정 글자, 높이 48px, 좌우 22px, 모서리 24px. 여러 개면 12px 간격으로 가운데 나란히.
- **강조 버튼** — 노랑 바탕·검정 글자 13px 굵게. 화면에서 가장 중요한 행동 하나에만.
- **외곽선 버튼** — 검정 바탕·1px `#F3F3F3` 선·12px `#F3F3F3` 글자·모서리 20px, 오른쪽에 흰 ↗ 화살표. 「바로가기」 같은 보조 이동.
- **보조 버튼** — `#333` 면·흰 글자, 높이 40px, 모서리 24px. 누르면 `#4A4A4A`.
- **탭** — 알약형, 높이 51px, 좌우 24px. 선택 = 흰 면/검정 글자, 미선택 = `#333`/`#A8A8A8`.
- **카드** — `#333` 면, 모서리 24px, 안쪽 32px, 그림자·테두리 없음. 위에서부터 [분류 칩] → 제목 26px 굵게 흰색 3줄 → 해시태그 `#A8A8A8` → 하단 사진(카드 폭 가득).
- **분류 칩** — 검정 바탕·흰 글자 14px, 모서리 8px. 회색 카드 위에서 검정 칩이 박혀 보인다(라이트의 「회색 카드 위 흰 칩」을 뒤집은 것).
- **목록 행** — 맨 위 1px `#F3F3F3` 밝은 선으로 시작, 행 사이 1px `#333` 선, 행 높이 65px, 오른쪽 끝에 32px 원형 `#333` ↗ 버튼(흰 화살표).
- **원형 아이콘 버튼** — 48px(슬라이드 이전·다음·정지) 또는 32px(바로가기), `#333` 면·흰 아이콘. 사이트 다크 모드에서 강조 상태는 흰 면·검정 아이콘, 비활성은 `#666` 아이콘.
- **상단 히어로 띠** — `#111` 면, 위아래 100px, 가운데 정렬 제목 48px 흰색 + 버튼 줄.
- **검색창** — `#333` 바탕·흰 글자·2px 흰 테두리·모서리 24px, 왼쪽 돋보기, 오른쪽 원형 지우기 버튼.
- **구분선** — 일반 1px `#333`, 섹션 시작 1px `#F3F3F3`.
- **분류 색 면** — 분홍·파랑·보라·주황은 모서리 8px의 작은 면·일러스트 바탕으로만 쓰고, 그 위에 글자를 얹지 않는다.
- **해시태그 줄** — `#키워드` 형태 14 ~ 16px `#A8A8A8`, 사이 8px.

### 움직임

- 기본 전환 **0.3s ease**(색·투명도), 메뉴·슬라이드 이동 **0.28s `cubic-bezier(0.4, 0, 0.2, 1)`**.
- 자동으로 넘어가는 영역에는 **항상 정지 버튼**을 둔다. 사용자가 움직임 줄이기를 켜면 애니메이션을 끈다.

## Do's and Don'ts

**Do**

- 공지 바깥 상자에 `#000` 바탕을 직접 칠하고, 글자는 흰색·회색 단계로 위계를 나눈다. 제목 `#FFFFFF`, 본문 `#D4D4D4`, 설명 `#A8A8A8`, 날짜 `#888`.
- 노랑은 화면에서 가장 중요한 행동 1~2곳에만 쓰고, 노랑 위 글자는 항상 검정으로 한다.
- 제목은 크고(본문의 2배 이상) 굵게(700), 자간은 음수로 좁힌다.
- 섹션 사이를 120px 이상 비운다. 채우기보다 비우는 쪽을 택한다.
- 버튼·탭·메뉴는 알약형, 카드는 24px 모서리로 통일한다.
- 선택 상태는 **흰 면 + 검정 글자 반전** 하나로 표시한다.
- 구분은 면 색(`#333`)과 1px 선으로만 한다.

**Don't**

- 라이트 값(흰 바탕·`#F3F3F3` 카드·`#333` 글자)을 섞지 않는다. 특히 `#333`은 다크에서 **면 색**이지 글자 색이 아니다.
- `#666` 이하로 어두운 회색을 읽어야 하는 글자에 쓰지 않는다.
- 라이트 링크 색 `#104ADF`를 쓰지 않는다 — 검정 위에서 보이지 않는다. 링크는 `#489FF8`.
- 그림자·그라데이션·두꺼운 테두리 상자를 쓰지 않는다.
- 노랑을 넓은 배경·여러 버튼·본문 글자에 흩뿌리지 않는다.
- 보조 강조 색(분홍·파랑·보라·주황)을 버튼이나 본문 색으로 쓰지 않는다.
- 굵기를 400·700 외에 섞지 않는다.
- 각진 모서리(0 ~ 4px) 버튼을 쓰지 않는다.
- 원본 사이트의 로고·캐릭터·서비스 아이콘·사진·문구를 가져오지 않는다. 원본의 자체 서체(웹폰트)도 쓰지 않는다 — 시스템 고딕으로 대체한다.
- 이 파일을 해당 회사의 공식 디자인 시스템이라고 소개하지 않는다.

## 라이트 원본 대조표 (참고)

2026-10-23 실측 라이트 값. 같은 토큰 이름의 다크 값과 짝지어 둔다. 라이트로 되돌려 쓸 때만 본다.

| 토큰 | 라이트 | 다크(이 파일 기준) |
|---|---|---|
| `background` | `#FFFFFF` | `#000000` |
| `foreground` | `#000000` | `#FFFFFF` |
| `text-strong` | `#111111` | `#F3F3F3` |
| `text-body` | `#333333` | `#D4D4D4` |
| `text-secondary` | `#666666` | `#A8A8A8` |
| `text-tertiary` | `#888888` | `#888888` |
| `text-muted` | `#A1A1A1` | `#666666` |
| `surface` (카드) | `#F3F3F3` | `#333333` |
| `surface-subtle` (히어로 띠) | `#F7F7F7` | `#111111` |
| `chip` | `#EEEEEE` | `#4A4A4A` |
| `border` / `border-strong` | `#EEEEEE` / `#111111` | `#333333` / `#F3F3F3` |
| 반전(선택·주 버튼) | 검정 면 + 흰 글자 | 흰 면 + 검정 글자 |
| `link` | `#104ADF` | `#489FF8` |
| `error` / `error-surface` | `#FF0919` / `#FFE9E9` | `#FF4D5A` / `#3A1418` |
| `accent-yellow` / `on-accent` | `#FAE100` / `#000000` | 같음 |
