---
version: alpha
name: Midnight Gallery Mono
description: 브랜드 컴퍼니 사이트(makervil.com) 메인·서브 9개 화면의 실측 스타일에서 뽑은 참고용 디자인 기준. 거의 검정(#111111) 바탕에 흰 글자와 흰색 투명도 단계만으로 위계를 나누고, 화면 끝까지 닿는 아주 큰 제목·각진 면·얇은 선·흑백 사진으로 전시장 같은 화면을 만든다. 색은 사진에서만 나온다. 해당 회사의 공식 디자인 시스템이 아니다.
colors:
  primary: "#FFFFFF"
  secondary: "#AEAEAE"
  tertiary: "#3A3A3A"
  neutral: "#111111"
  background: "#111111"
  foreground: "#FFFFFF"
  text-body: "#CBCBCB"
  text-secondary: "#AEAEAE"
  text-tertiary: "#969696"
  text-meta: "#8C8C8C"
  surface: "#191919"
  surface-raised: "#1F1F1F"
  chip-active: "#3A3A3A"
  border: "#373737"
  border-field: "#4C4C4C"
  border-strong: "#757575"
  footer: "#000000"
  inverse-background: "#FFFFFF"
  inverse-foreground: "#111111"
typography:
  display-xl:
    fontFamily: Apple SD Gothic Neo
    fontSize: 172px
    fontWeight: 400
    lineHeight: 172px
    letterSpacing: -5.2px
  display-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 132px
    fontWeight: 400
    lineHeight: 132px
    letterSpacing: -4px
  stat-number:
    fontFamily: Apple SD Gothic Neo
    fontSize: 93px
    fontWeight: 400
    lineHeight: 93px
    letterSpacing: -1.86px
  headline-xl:
    fontFamily: Apple SD Gothic Neo
    fontSize: 89px
    fontWeight: 600
    lineHeight: 98px
    letterSpacing: -1.8px
  headline-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 62px
    fontWeight: 600
    lineHeight: 69px
    letterSpacing: -2.4px
  headline-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 60px
    fontWeight: 400
    lineHeight: 60px
    letterSpacing: -2.1px
  headline-sm:
    fontFamily: Apple SD Gothic Neo
    fontSize: 48px
    fontWeight: 600
    lineHeight: 55px
    letterSpacing: -1.44px
  title-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 36px
    fontWeight: 600
    lineHeight: 40px
    letterSpacing: -0.72px
  title-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 27px
    fontWeight: 600
    lineHeight: 31px
    letterSpacing: -0.68px
  title-sm:
    fontFamily: Apple SD Gothic Neo
    fontSize: 22px
    fontWeight: 600
    lineHeight: 28px
    letterSpacing: -0.44px
  title-xs:
    fontFamily: Apple SD Gothic Neo
    fontSize: 17px
    fontWeight: 600
    lineHeight: 24px
    letterSpacing: 0px
  body-lg:
    fontFamily: Apple SD Gothic Neo
    fontSize: 18px
    fontWeight: 600
    lineHeight: 23px
    letterSpacing: -0.54px
  body-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 16px
    fontWeight: 400
    lineHeight: 26px
    letterSpacing: 0px
  body-sm:
    fontFamily: Apple SD Gothic Neo
    fontSize: 15px
    fontWeight: 400
    lineHeight: 21px
    letterSpacing: 0px
  label-md:
    fontFamily: Apple SD Gothic Neo
    fontSize: 14px
    fontWeight: 600
    lineHeight: 17px
    letterSpacing: 0px
  label-caps:
    fontFamily: Apple SD Gothic Neo
    fontSize: 14px
    fontWeight: 600
    lineHeight: 18px
    letterSpacing: 0.35px
  caption:
    fontFamily: Apple SD Gothic Neo
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: -0.28px
rounded:
  none: 0px
  pill: 999px
spacing:
  xxs: 4px
  xs: 6px
  sm: 12px
  md: 24px
  lg: 30px
  xl: 48px
  xxl: 96px
  section-sm: 120px
  section: 150px
  page-padding: 20px
  grid-gap: 12px
  header-height: 72px
  container: 1400px
components:
  page:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.text-body}"
    typography: "{typography.body-md}"
  header:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.caption}"
    height: 72px
  page-title:
    textColor: "{colors.foreground}"
    typography: "{typography.display-xl}"
  section-label:
    textColor: "{colors.foreground}"
    typography: "{typography.label-md}"
  section-title:
    textColor: "{colors.foreground}"
    typography: "{typography.headline-lg}"
  statement:
    textColor: "{colors.foreground}"
    typography: "{typography.headline-sm}"
  stat:
    textColor: "{colors.foreground}"
    typography: "{typography.stat-number}"
  stat-label:
    textColor: "{colors.foreground}"
    typography: "{typography.body-sm}"
  link-cta:
    textColor: "{colors.foreground}"
    typography: "{typography.caption}"
    padding: 0 0 12px
  link-cta-underline:
    backgroundColor: "{colors.foreground}"
    height: 1px
  button-primary:
    backgroundColor: "{colors.inverse-background}"
    textColor: "{colors.inverse-foreground}"
    typography: "{typography.label-md}"
    rounded: "{rounded.none}"
    padding: 0 22px
    height: 60px
  filter-chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-tertiary}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    padding: 3px
    height: 36px
  filter-chip-active:
    backgroundColor: "{colors.chip-active}"
    textColor: "{colors.foreground}"
    typography: "{typography.label-md}"
    rounded: "{rounded.none}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.none}"
    padding: 30px
  card-title:
    textColor: "{colors.foreground}"
    typography: "{typography.title-md}"
  card-meta:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-meta}"
    typography: "{typography.label-caps}"
  card-description:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.body-sm}"
  metric-card:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.foreground}"
    typography: "{typography.title-xs}"
    rounded: "{rounded.none}"
    padding: 24px
  service-card-title:
    textColor: "{colors.foreground}"
    typography: "{typography.title-lg}"
  step-title:
    textColor: "{colors.foreground}"
    typography: "{typography.title-sm}"
  step-number:
    textColor: "{colors.text-tertiary}"
    typography: "{typography.title-sm}"
  news-card-title:
    textColor: "{colors.foreground}"
    typography: "{typography.body-lg}"
  news-card-date:
    textColor: "{colors.text-secondary}"
    typography: "{typography.caption}"
  image-tag:
    backgroundColor: "{colors.chip-active}"
    textColor: "{colors.foreground}"
    typography: "{typography.caption}"
    rounded: "{rounded.none}"
    padding: 2px 6px
  list-row:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.body-md}"
    padding: 0 9px
    height: 76px
  list-row-divider:
    backgroundColor: "{colors.border-strong}"
    height: 1px
  timeline-year:
    textColor: "{colors.foreground}"
    typography: "{typography.headline-sm}"
  timeline-event:
    textColor: "{colors.foreground}"
    typography: "{typography.caption}"
  divider:
    backgroundColor: "{colors.border}"
    height: 1px
  form-field:
    textColor: "{colors.foreground}"
    typography: "{typography.label-md}"
    padding: 24px 0 12px
  form-field-underline:
    backgroundColor: "{colors.border-field}"
    height: 1px
  page-subtitle:
    textColor: "{colors.foreground}"
    typography: "{typography.display-lg}"
  english-heading:
    textColor: "{colors.foreground}"
    typography: "{typography.headline-md}"
  hero-statement:
    textColor: "{colors.foreground}"
    typography: "{typography.headline-xl}"
  indicator-dot:
    backgroundColor: "{colors.foreground}"
    rounded: "{rounded.pill}"
    size: 8px
  footer:
    backgroundColor: "{colors.footer}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.caption}"
  footer-heading:
    textColor: "{colors.foreground}"
    typography: "{typography.label-md}"
---

# Design System: Midnight Gallery Mono

> **출처·성격**: 브랜드 컴퍼니 사이트 [makervil.com/en](https://www.makervil.com/en)의 메인과 서브 8개 화면(About·Brands·브랜드 상세·Ecosystem·Insights 목록·Insights 상세·Careers·Contact)을 2026-10-27에 PC(1440px)·모바일(390px)로 열어 **계산된 스타일 값을 직접 재서** 정리한 참고 기준이다. 한글 화면 값은 같은 사이트의 한국어판(메인·About·Insights·Careers)에서 함께 쟀다. **해당 회사의 공식 디자인 시스템이 아니다.** 로고·브랜드명·제품 사진·3D 그래픽·문구는 넣지 않았고, 색·글자 크기·여백·모서리 같은 **수치와 규칙만** 옮겼다.

## Overview

불을 끈 전시장에 작품만 조명을 받는 화면이다. 바탕은 순검정이 아닌 **거의 검정(`#111111`)**, 글자는 흰색이고, 색은 쓰지 않는다. 위계는 **흰색의 투명도 단계**(100% → 78% → 66% → 56% → 42%)로만 나눈다. 화면에 들어오는 색은 전부 **사진**에서 나온다 — 그래서 사진이 작품처럼 보인다.

인상을 만드는 요소는 네 가지다.

1. **화면 끝까지 닿는 거대한 제목** — 서브 화면 첫 제목은 화면 너비의 12%(1440px에서 172px), 영문 대문자 한 단어로 왼쪽 끝부터 꽉 채운다. 굵기는 400 — 크기로만 압도한다.
2. **각진 면** — 카드·버튼·칩·사진 어디에도 둥근 모서리가 없다(0px). 둥근 것은 작은 점 표시뿐이다.
3. **얇은 선과 아주 옅은 면** — 구분은 흰색 16~42% 투명도의 1px 선, 카드는 바탕보다 한 톤 밝은 면(`#191919`)으로만 한다. 그림자는 없다.
4. **괄호 라벨 + 비대칭 배치** — 섹션마다 `(About Us)`처럼 괄호로 감싼 작은 라벨을 왼쪽 첫 칸에 두고, 큰 제목은 그 오른쪽에서 시작해 다음 줄부터 화면 왼쪽 끝으로 흘러간다.

## Colors

### 바탕과 면 — 검정 4단계

| 토큰 | 값 | 쓰임 | 이유 |
|---|---|---|---|
| `background` | `#111111` | 페이지 전체 바탕 | 실측 면적 1위. 순검정보다 한 톤 밝아 사진의 어두운 부분이 바탕과 붙지 않는다 |
| `surface` | `#191919` | 카드·비선택 칩 | 원본은 흰색 3.5% 투명 면. 테두리 없이 면만으로 「한 덩어리」를 만든다 |
| `surface-raised` | `#1F1F1F` | 수치 카드 | 원본은 흰색 6% 투명 면 — 카드보다 한 단계 앞 |
| `chip-active` | `#3A3A3A` | 선택된 칩·사진 위 분류 표시 | 원본은 흰색 17% 투명 면. 선택 상태를 색 대신 밝기로 표시 |
| `footer` | `#000000` | 바닥글 | 페이지가 끝났다는 신호를 순검정 한 번으로 준다 |

### 글자 — 흰색 투명도 5단계

| 토큰 | 값 (원본 투명도) | 쓰임 | 이유 |
|---|---|---|---|
| `foreground` | `#FFFFFF` (100%) | 제목·메뉴·목록 제목·버튼 글자 | 실측 글자 색 1위(전체 글자의 약 80%) |
| `text-body` | `#CBCBCB` (78%) | 기사 본문 | 긴 글은 순백보다 눈부심이 덜하다 |
| `text-secondary` | `#AEAEAE` (66~68%) | 설명문·날짜 | 「읽어도 되고 안 읽어도 되는」 정보 |
| `text-tertiary` | `#969696` (56%) | 비선택 칩·연도·단계 번호 | 꺼진 상태 표시 |
| `text-meta` | `#8C8C8C` | 카드 머리 분류(대문자 라벨) | 원본은 42%(`#757575`)지만 어두운 면 위 대비가 4:1에 못 미쳐 **읽기용으로 한 단계 올렸다** |

### 선

| 토큰 | 값 (원본 투명도) | 쓰임 |
|---|---|---|
| `border` | `#373737` (16%) | 카드 위 구분선·서비스 묶음 테두리 |
| `border-field` | `#4C4C4C` (25%) | 입력칸 밑줄 |
| `border-strong` | `#757575` (42%) | 뉴스 목록의 위·행 사이 선 |

### 반전 — 단 한 곳

`inverse-background #FFFFFF` + `inverse-foreground #111111` = **흰 바탕 버튼**(문의 보내기). 어두운 화면에서 흰 면은 그 자체로 가장 강한 신호라, 페이지당 1개만 쓴다.

### 강조 색 — 없음

이 기준에는 **브랜드 강조 색이 없다.** 빨강·파랑 같은 색을 버튼·제목·라벨에 넣지 않는다. 색이 필요한 곳은 사진에 맡긴다. 거대한 배경 문구(흰색 28% ≈ `#545454`)는 장식이므로 정보를 담지 않는다.

### 밝은 화면(라이트 모드)

사이트는 밝은 화면 전환도 제공하는데, 바탕 채널과 글자 채널을 **그대로 맞바꾼다** — 바탕 `#FFFFFF`, 글자 `#111111`, 투명도 단계는 그대로(본문 = 검정 78% 등). 밝은 공지가 필요하면 위 표의 흰/검정만 뒤집고 단계 비율은 유지한다.

## Typography

원본 사이트는 영문용 자체 서체(굵기 400·600)와 한글용 웹폰트를 쓴다. **이 파일은 그 서체들을 쓰지 않는다** — 대신 운영체제 기본 고딕(`"Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", sans-serif`)으로 같은 크기·굵기·자간을 맞춘다. 원본도 한글 뒤에 시스템 글꼴을 대체 글꼴로 지정해 두었다.

**영문 큰 제목은 굵기 400, 한글 제목은 굵기 600** — 원본 사이트가 한국어판에서 제목만 600으로 올린다. 같은 크기에서 한글 획이 영문보다 가늘어 보이기 때문이다.

### 단계 (PC 1440px → 모바일 390px)

| 토큰 | PC | 모바일 | 쓰임 |
|---|---|---|---|
| `display-xl` | 172 / 172, 400, -3% | 100 / 100 | 서브 화면 첫 제목(영문 대문자 한 단어) |
| `display-lg` | 132 / 132, 400, -3% | 60 / 60 | 목록 화면 제목·오른쪽 끝 개수 숫자 |
| `stat-number` | 93 / 93, 400, -2% | 54 / 54 | 큰 수치(단위 글자는 60px로 작게) |
| `headline-xl` | 89 / 98, 600, -2% | 31 / 36 | 메인 첫 선언 문장(한글) |
| `headline-lg` | 62 / 69, 600, -4% | 33 / 38 | 섹션 제목(한글) |
| `headline-md` | 60 / 60, 400, -3.5% | 44 ~ 50 | 섹션 제목(영문 짧은 말) |
| `headline-sm` | 48 / 55, 600, -3% | 26 / 30 | 소개 문단·연표 연도 |
| `title-lg` | 36 / 40, 600, -2% | 26 / 28 | 서비스 카드 제목 |
| `title-md` | 27 / 31, 600, -2.5% | 28 / 32 | 카드 제목 |
| `title-sm` | 22 / 28, 600, -2% | 22 / 28 | 단계 제목·단계 번호 |
| `title-xs` | 17 / 24, 600 | 17 / 24 | 수치 카드 제목 |
| `body-lg` | 18 / 23, 600, -3% | 18 / 24 | 뉴스 카드 제목 |
| `body-md` | 16 / 26, 400 | 16 / 26 | 기사 본문·목록 행 |
| `body-sm` | 15 / 21, 400 | 15 / 21 | 설명문·수치 설명 |
| `label-md` | 14 / 17, 600 | 14 / 17 | `(About Us)` 괄호 라벨·버튼·입력칸 이름 |
| `label-caps` | 14 / 18, 600, +0.35px, 대문자 | 같음 | 카드 머리 분류(상시 채용 · 정규직) |
| `caption` | 14 / 20, 400, -0.28px | 같음 | 메뉴·날짜·연표 항목·바닥글 |

### 규칙

- **제목 크기는 화면 너비에 비례한다.** 원본은 거의 모든 글자 크기를 `max(최소값, 화면 비율)`로 정한다(첫 제목 = 너비의 12%, 섹션 제목 ≈ 4.3%). 본문 폭이 좁은 화면에서는 위 표의 PC 값을 그대로 쓰지 말고 같은 비율로 줄인다 — 예: 폭 1000px이면 첫 제목 ≈ 120px.
- **큰 글자일수록 자간을 더 좁힌다.** 본문 0, 카드 제목 -2%, 섹션 제목 -3 ~ -4%, 첫 제목 -3%. 원본 한국어판 제목 자간은 -0.02 ~ -0.04em.
- **제목 줄 간격은 1.0 ~ 1.15배로 촘촘하게**, 본문은 1.65배(16/26).
- **한글 제목은 낱말 단위로 줄을 바꾼다**(`word-break: keep-all`). 원본 한국어판 제목 전부에 적용돼 있다.
- **영문 짧은 말과 한글 문장을 섞는다.** 화면 첫 제목·섹션 라벨·버튼은 영문(ABOUT, `(Our Story)`, More About Us), 설명과 문단은 한글. 영문은 굵기 400, 한글은 600.
- 굵기는 **400·600 두 개**만 쓴다(원본 수치 단위 글자만 500).

## Layout

### 반응형 기준

| 구간 | 너비 | 좌우 여백 |
|---|---|---|
| 데스크톱 | 1440px 이상 | 20px (1920px보다 넓으면 너비의 1.04%로 늘어남) |
| 노트북·태블릿 | 768 ~ 1439px | 20px |
| 모바일 | 767px 이하 | 20px |

### 그리드·여백

- **본문 폭 = 화면 전체.** 가운데 좁은 상자를 두지 않고 좌우 20px만 남긴 채 끝까지 쓴다(1440px에서 1400px). 거대한 제목이 화면 끝에 닿는 인상이 여기서 나온다.
- **12칸 그리드, 칸 사이 12px.** 카드 폭은 이 그리드를 그대로 따른다 — 4열(341px) · 3열(459px) · 2열(694px).
- **비대칭 배치** — 괄호 라벨은 첫 칸, 제목 첫 줄은 셋째 칸부터 들여 쓰고 둘째 줄부터 왼쪽 끝으로 흐른다. 설명 문단은 오른쪽 절반 안쪽(약 460px 폭)에 좁게 둔다.
- **사진은 지그재그로 흩뜨린다** — 메인 브랜드 목록은 사진 세 장을 왼쪽 위·오른쪽 중간·가운데 아래에 엇갈려 놓고, 사진 아래 왼쪽에 이름·오른쪽에 연도를 단다.
- 섹션 위아래 **150px**(메인), **96px**(서브), 묶음 사이 **120px**. 서브 화면 첫 섹션 위 여백은 화면 너비의 6.7%(1440px에서 96px).
- 헤더 높이 72px. 로고는 왼쪽, 화면 밝기 전환은 가운데, 메뉴 6개(14px)는 오른쪽.
- 모바일은 대부분 1열로 쌓이고(큰 수치 4개는 2×2), 괄호 라벨은 제목 바로 위로 올라가며 제목 들여쓰기가 사라진다.

## Elevation & Depth

**그림자를 쓰지 않는다.** 실측한 화면에 카드·버튼 그림자가 없다(떠 있는 작은 표시 몇 곳에만 아주 옅은 그림자). 깊이는 다음 두 가지로만 만든다.

1. **밝기 단계** — `#111111` 바탕 → `#191919` 카드 → `#1F1F1F` 수치 카드 → `#3A3A3A` 선택 칩. 앞에 올수록 한 단계씩 밝다.
2. **사진** — 흑백·저채도 사진과 투명 유리 같은 3D 오브제가 화면의 유일한 입체감이다. 사진 위아래에 바탕색(`#111111`)으로 녹아드는 그라데이션을 깔아 경계를 지운다.

## Shapes

| 토큰 | 값 | 쓰임 |
|---|---|---|
| `none` | 0px | 카드·버튼·칩·사진·입력칸 — **전부** |
| `pill` | 999px | 슬라이드 위치 점·화면 밝기 전환 스위치 |

**규칙**: 모서리는 0px로 통일한다. 둥근 모서리가 하나라도 섞이면 이 기준의 날카로운 인상이 무너진다. 사진은 잘라 쓰되 모서리를 깎지 않는다.

## Components

- **헤더** — 바탕과 같은 `#111111`, 높이 72px, 아래 선 없음. 메뉴 글자 14px 흰색.
- **화면 첫 제목** — 영문 대문자 한 단어(ABOUT · INSIGHTS) 172px 굵기 400, 왼쪽 끝. 오른쪽 끝 같은 줄에 한 줄 소개(15px 600) 또는 개수 숫자(132px)를 둔다.
- **괄호 라벨** — `(About Us)` 형식, 14px 굵기 600 흰색. 모든 섹션의 시작 표시.
- **화살표 링크** — 글자 14px + 오른쪽 끝 `→`, 아래 12px 띄워 1px 흰 밑줄. 폭은 글자보다 넓게(약 160 ~ 200px) 잡아 밑줄이 「버튼 바닥」처럼 보이게 한다. 마우스를 올리면 밑줄이 왼쪽부터 다시 그려진다.
- **주 버튼** — 흰 면·`#111111` 글자 14 ~ 15px 굵기 600, 높이 60px, 좌우 22px, 모서리 0. 페이지당 하나.
- **큰 수치** — 숫자 93px 굵기 400 + 단위(억·B·M·+) 60px. 아래 설명 15px. 네 개를 4열로 나란히.
- **수치 카드** — `#1F1F1F` 면, 안쪽 24px, 위 큰 숫자 → 1px 구분선 → 제목 17px 600 → 설명 15px `#AEAEAE`. 네 장을 계단처럼 높이를 엇갈려 배치한다.
- **카드** — `#191919` 면, 안쪽 30px, 모서리·테두리·그림자 없음. 위에서부터 [대문자 분류 `#8C8C8C`] → 제목 27px → (아래 여백) → 항목 이름(대문자 14px) + 값(14px) 2열 → `지원하기 →` 링크.
- **서비스 카드** — 3열, 위 절반은 `#191919` 면에 제목 36px + 설명, 아래 절반은 사진이 카드 폭 가득.
- **뉴스 카드** — 사진(카드 폭 가득, 약 16:9) 오른쪽 위에 분류 표시(`#3A3A3A` 면 흰 글자 14px), 사진 아래 날짜 14px `#AEAEAE` → 제목 18px 600 두 줄.
- **분류 칩** — 이름 + 개수 묶음, 높이 36px. 선택 = `#3A3A3A` 면 흰 글자 600, 미선택 = `#191919` 면 `#969696` 글자. 칩 사이 6px.
- **목록 행** — 맨 위·행 사이 1px `#757575` 선, 행 높이 76px, 왼쪽 제목 16px, 오른쪽 끝 날짜 14px.
- **연표** — 왼쪽에 연도 48px, 오른쪽에 월(14px)·사건(14px) 행을 10px 간격으로 쌓는다. 연도 묶음 사이 120px.
- **단계 목록** — 왼쪽 번호 `01`(22px `#969696`), 오른쪽 단계 제목 22px + 설명 15px. 단계 사이 36px. 반대편 절반에 사진 한 장.
- **입력칸** — 테두리 상자 없이 아래 1px `#4C4C4C` 밑줄만, 이름 15px 600, 위 24px·아래 12px 여백.
- **바닥글** — 순검정 `#000000`, 회사 정보·연락처를 작은 글자(14px `#AEAEAE`)로 열 나눠 둔다.

### 움직임

- 나타나기: 투명도 0.56s + 위로 이동 0.7s, `cubic-bezier(0.16, 1, 0.3, 1)` — 빠르게 시작해 아주 천천히 멈춘다. 사진은 `clip-path`로 0.85s에 걸쳐 열린다.
- 밑줄: 0.32s `cubic-bezier(0.22, 1, 0.36, 1)`로 왼쪽부터 그려진다.
- 밝기 전환: 0.68s.
- 사용자가 움직임 줄이기를 켜면 애니메이션을 끈다. 움직임이 없어도 화면이 완성돼 보이게 만든다.

## Do's and Don'ts

**Do**

- 바탕은 `#111111`, 글자는 흰색과 흰색 투명도 단계(78·66·56%)로 위계를 나눈다.
- 서브 화면 첫 제목은 영문 대문자 한 단어를 화면 폭 가득(너비의 약 12%) 크게 쓴다.
- 섹션마다 `(라벨)` 괄호 라벨을 왼쪽에 두고, 제목은 그 오른쪽에서 시작한다.
- 한글 제목은 굵기 600·자간 -3%·줄 간격 1.1배·낱말 단위 줄바꿈으로 쓴다.
- 카드·버튼·칩·사진의 모서리는 0px로 통일한다.
- 구분은 1px 선(흰색 16 ~ 42%)과 한 톤 밝은 면(`#191919`)으로만 한다.
- 색은 사진에 맡긴다. 사진은 흑백·저채도로 톤을 맞춘다.
- 흰 바탕 버튼은 페이지에서 가장 중요한 행동 하나에만 쓴다.

**Don't**

- 빨강·파랑 같은 강조 색을 버튼·제목·라벨에 넣지 않는다.
- 그림자·둥근 모서리·두꺼운 테두리 상자를 쓰지 않는다.
- 순검정(`#000000`)을 페이지 바탕으로 쓰지 않는다 — 바닥글에만 쓴다.
- 흰색 42% 미만의 글자로 정보를 전달하지 않는다(배경 장식 문구만 예외).
- 본문을 가운데 좁은 상자에 가두지 않는다 — 화면 폭 끝까지 쓴다.
- 굵기를 400·600 외에 섞지 않는다.
- 원본 사이트의 로고·브랜드명·제품 사진·3D 오브제·문구를 가져오지 않는다. 원본의 자체 서체(웹폰트)도 쓰지 않는다 — 시스템 고딕으로 대체한다.
- 이 파일을 해당 회사의 공식 디자인 시스템이라고 소개하지 않는다.
