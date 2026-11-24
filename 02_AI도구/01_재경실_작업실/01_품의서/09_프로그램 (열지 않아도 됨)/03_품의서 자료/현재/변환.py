# -*- coding: utf-8 -*-
"""품의서 HTML 변환 — 품의서 원문을 전자결재에 붙여넣을 HTML로 바꾼다. AI 를 쓰지 않는다.

    python 변환.py <파일>        품의서마다 줄번호를 붙인 결과를 화면에 보여 준다 (파일은 만들지 않는다)

이 프로그램은 파일을 읽고 HTML 글자만 돌려준다. 파일을 만들거나 지우는 코드, 다른 프로그램 · 인터넷을 쓰는 코드는 넣지 않는다.
(「품의서 만들기」가 실행 전에 검사해 이런 코드가 있으면 쓰지 않는다)

읽는 형식
- txt · md        utf-8 / utf-8(BOM) / cp949 / utf-16. md 의 # · ** · 목록 기호는 지우고 구조만 쓴다
- docx            워드 자동 번호(numbering.xml)를 글자로 되살리고, 문단 들여쓰기를 앞 공백으로, 표 칸 병합을 살린다
- pptx            슬라이드 하나 = 품의서 한 건 (「아래」 줄이 있는 슬라이드). 그 슬라이드의 글상자 · 표를 위치 순서로 잇는다
- xlsx            시트 하나 = 품의서 한 건. 칸이 2개 이상 찬 줄이 이어지면 표, 아니면 글줄
- pdf             글자층이 있는 pdf (lib 폴더의 pypdf 사용). 스캔 pdf 는 읽지 못한다
- hwpx · rtf      글줄과 표
- doc · ppt · xls · hwp   옛 형식은 읽지 않는다 (docx · pptx · xlsx · hwpx 로 다시 저장해 넣도록 알린다)
- 글자로 쓴 표     | 칸 | 칸 |  ·  칸 | 칸 (양끝 없음, 2줄 이상)  ·  탭으로 나눈 줄  ·  ┌─┬─┐ 괘선  ·  두 칸 이상 공백으로 맞춘 줄(3칸 3줄 이상)
                  표 칸 글자가 << 이면 왼쪽 칸과 합친 칸, ^^ 이면 위 칸과 합친 칸

바꾸는 법 (품의서_작성규칙.md 의 재경실 Guide · 품의서_HTML틀.html 과 같은 모양)
- 번호는 기호 모양이 아니라 깊이로 다시 매긴다 : 1. > 가. > (1) > (가) > - > ·  (□ → 1. · ○ → 가. · - 는 그대로)
  원문에서 처음 나온 기호가 깊이 1, 그 아래에 처음 나온 다른 기호가 깊이 2 … 번호 값(1 → 가, 3 → 다)은 그대로 옮긴다
  앞뒤 줄과 같은 기호(- · □ ○)인데 그 줄만 들여쓰기가 1~3칸 다르고 세 줄 모두 「항목 : 값」이면 앞뒤 줄과 같은 단계로 본다
  들여쓰기가 거의 없는 품의서(본문 줄 90% 이상이 앞 공백 0)는 번호 · 기호로 단계를 정하고, 가. 줄 바로 다음 ( 덧붙임 줄은
  그 항목 글자 위치, [첨 부] 같은 괄호 이름 줄은 마지막 번호 단계 · 그 다음 줄들은 괄호 이름 뒤 글자 위치
- 깊이별 앞 공백 = 변환설정.json 의 깊이별_앞공백. 서두 · 붙임 = 깊이 1 위치. 번호 없는 이어짐 줄 = 윗 항목 글자 위치
- 「아래」 줄 변형(- 아 래 -, -다음-, === 아 래 ===, 【아래】, 가운데 정렬 …)은 Guide 「아래」 줄로. 원문에 없으면 넣지 않는다
- 빈 줄은 본문 맨 위 · 서두 다음 · 「아래」 줄 다음 · 큰 번호 사이 · 붙임 앞에만 한 줄
- 끝 표시 변형(끝 · .끝 · - 끝 - · 이상. …)은 마지막 줄 끝에 두 칸 띄우고 「끝.」. 표로 끝나면 표 아래 줄. 끝. 뒤의 줄은 뺀다
- 날짜 · 금액 · 번호 값은 고치지 않는다 (건너뛴 번호 등은 기록에 알림만)
- 한 줄 = <p style="글꼴 · 크기 · 줄간격"> 하나, 빈 줄 = <p style="…"><br></p>, 줄 앞 공백 · 두 칸 이상 공백 = &nbsp;, 표 = <table border="1">
  글꼴 · 크기 · 줄간격 = 변환설정.json 의 문단_스타일 (Guide : 본고딕 · 12pt · 줄간격 1.5)
- 한 줄이 전자결재 한 줄 폭(한줄_최대폭)을 넘으면 띄어쓰기 자리에서 미리 나눈다. 나눈 다음 줄은 번호 뒤 글자 위치에서 시작
바꿀 수 있는 값은 같은 폴더의 변환설정.json 에 있다. Python 표준 라이브러리만 쓴다 (pdf 만 lib 폴더의 pypdf).
평소에는 「품의서 만들기.bat」이 이 프로그램을 부른다.
"""
import datetime
import html
import json
import posixpath
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
CONFIG, LIB = ROOT / "변환설정.json", ROOT / "lib"
SUPPORTED = (".txt", ".md", ".docx", ".pptx", ".xlsx", ".pdf", ".hwpx", ".rtf", ".doc", ".ppt", ".xls", ".hwp")
PICTURES = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".webp", ".emf", ".wmf")

# 변환설정.json 이 없을 때 쓰는 값 (없으면 이 값으로 새로 만든다)
DEFAULT = {
    "_설명": {
        "아래줄_찾기": "원본에서 「아래」 줄로 보는 모양 (정규식, 줄 앞뒤 공백을 지운 뒤 비교). - 아 래 - · -다음- · === 아 래 === · 【아래】 · 아  래 등",
        "아래줄_앞공백": "「아래」 줄 앞에 넣는 공백 칸 수 (가운데 정렬 대신 앞 공백으로 가운데쯤)",
        "아래줄_모양": "바꿔 쓸 「아래」 줄",
        "아래줄_없으면_넣기": "원문에 「아래」 줄이 없을 때 서두 다음에 넣을지 (true / false)",
        "맨위_빈줄": "본문 맨 위를 한 칸 띄울지 (true / false)",
        "깊이별_앞공백": "번호 깊이 1 · 2 · 3 … 줄의 앞 공백 칸 수. 서두 · 붙임은 깊이 1 위치. 목록보다 깊으면 마지막 값에 3칸씩 더한다",
        "번호_모양": "깊이 1 · 2 · 3 … 에 쓰는 번호. 1 자리에 숫자, 가 자리에 가나다가 들어간다. 목록보다 깊으면 마지막 모양",
        "하이픈_그대로": "원문의 - 줄은 깊이와 관계없이 - 로 둘지 (true). false 면 깊이에 맞는 번호로 바꾼다. - 아래의 - 는 · 로 쓴다",
        "탭_칸수": "줄 앞 탭 한 개를 공백 몇 칸으로 셀지 (깊이를 정할 때만 쓴다). 글자 사이 탭은 이 칸 수만큼 공백으로 바꾼다",
        "끝_앞공백": "「끝.」 앞에 띄우는 칸 수",
        "끝_없으면_넣기": "원문에 끝 표시가 없을 때 마지막 줄 끝에 「끝.」을 붙일지 (true / false)",
        "끝_따로줄이면_붙이기": "따로 줄로 쓴 끝 표시를 마지막 줄 끝으로 옮길지 (true). false 면 따로 줄로 「끝.」",
        "붙임_뒤_공백": "줄 처음의 「붙임」 · 「첨부」 · 「별첨」 다음 공백 칸 수 (괄호나 쌍점을 쓴 「(첨부)」 · 「첨부 :」 는 그대로)",
        "제목줄_빼기": "「제목 : …」 줄과 md 의 # 제목 줄을 본문에서 뺄지 (true / false)",
        "공백표_최소칸": "두 칸 이상 공백으로 맞춘 줄을 표로 볼 때 첫 줄의 칸 수 최소값",
        "공백표_최소줄": "두 칸 이상 공백으로 맞춘 줄을 표로 볼 때 이어지는 줄 수 최소값",
        "표_스타일": "표 모양. margin-left = 표가 시작하는 위치",
        "머리칸_스타일": "표 첫 줄(머리칸) 여백 · 글꼴. white-space:nowrap = 머리칸은 한 줄로",
        "칸_스타일": "표 칸 여백 · 글꼴. word-break:keep-all = 단어 중간에서 줄을 나누지 않음",
        "문단_스타일": "줄(<p>)마다 넣는 글꼴 · 글자 크기 · 줄간격 (전자결재 편집기가 쓰는 모양). 빈 문자열이면 넣지 않는다",
        "한줄_최대폭": "전자결재 한 줄에 들어가는 폭 (본고딕 12pt 한글 글자 수, 소수 가능. 전자결재 실측 48.2자는 한 줄 · 49자는 넘어감). 넘는 줄은 띄어쓰기 자리에서 미리 나눈다. 0 이면 나누지 않는다",
    },
    "아래줄_찾기": r"^[-=~_―─—–ㅡ<＜〈《\[【「(（*\s]*(아\s*래|다\s*음)[-=~_―─—–ㅡ>＞〉》\]】」)）*\s]*$",
    "아래줄_앞공백": 58,
    "아래줄_모양": "-----     아     래     -----",
    "아래줄_없으면_넣기": False,
    "맨위_빈줄": True,
    "깊이별_앞공백": [5, 8, 12, 16, 21, 24, 27, 30],
    "번호_모양": ["1.", "가.", "(1)", "(가)", "-", "·"],
    "하이픈_그대로": True,
    "탭_칸수": 4,
    "끝_앞공백": 2,
    "끝_없으면_넣기": True,
    "끝_따로줄이면_붙이기": True,
    "붙임_뒤_공백": 2,
    "제목줄_빼기": False,
    "공백표_최소칸": 3,
    "공백표_최소줄": 3,
    "표_스타일": "border-collapse:collapse;margin-left:40px",
    "머리칸_스타일": "padding:4px 8px;font-family:본고딕;font-size:12pt;white-space:nowrap",
    "칸_스타일": "padding:4px 8px;font-family:본고딕;font-size:12pt;word-break:keep-all",
    "문단_스타일": "font-family: 본고딕; font-size: 12pt; line-height: 1.5; margin-top: 0px; margin-bottom: 0px;",
    "한줄_최대폭": 48.5,
}


def load_config():
    cfg = dict(DEFAULT)
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8-sig")))
    return cfg


CFG = load_config()
AREA_FIND = re.compile(CFG["아래줄_찾기"])
AREA_LINE = " " * CFG["아래줄_앞공백"] + CFG["아래줄_모양"]
NOTES = []          # 변환하며 알게 된 것 (기록용. 품의서 내용은 넣지 않는다)


class 읽기안내(Exception):
    """사람에게 보여 줄 한 줄 안내 (이 파일을 읽지 못한 이유)"""


# ── 글자 모양 ──

KOR = "가나다라마바사아자차카타파하"
CIRC_NUM = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
CIRC_KOR = "㉮㉯㉰㉱㉲㉳㉴㉵㉶㉷㉸㉹㉺㉻"
CIRC_JAMO = "㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩㉪㉫㉬㉭"
ROMAN_U = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"
ROMAN_A = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
FULLWIDTH = {i: i - 0xFEE0 for i in range(0xFF01, 0xFF5F)}          # 전각 글자 → 반각 (번호를 알아볼 때만)
INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)

MARK = re.compile(r"""
    (?P<n1>\d{1,2})\.(?!\d)
  | (?P<n2>\d{1,2})\)
  | \((?P<n3>\d{1,2})\)
  | (?P<k1>[가나다라마바사아자차카타파하])\.
  | (?P<k2>[가나다라마바사아자차카타파하])\)
  | \((?P<k3>[가나다라마바사아자차카타파하])\)
  | (?P<c1>[①-⑳])
  | (?P<c2>[㉮-㉻])
  | (?P<c3>[㉠-㉭])
  | (?P<r1>[Ⅰ-Ⅹ])\.?
  | (?P<r2>VIII|VII|VI|IV|IX|III|II|I|V|X)\.(?=\s)
  | (?P<sq>[□■◆▶◼▪])(?=\s)
  | (?P<ci>[○◇▷●◦ㅇ])(?=\s)
  | (?P<da>[-–—‐‑－―ㅡ−](?![-–—‐‑－―ㅡ−\d]))(?:\s*\.(?!\.))?
  | (?P<dt>[·•∙ㆍ‧])
""", re.X)
BULLETS = ("□", "○", "-", "·")                                  # 번호 없는 기호 계열
FAMILY = {"n1": "1.", "n2": "1)", "n3": "(1)", "k1": "가.", "k2": "가)", "k3": "(가)", "c1": "①", "c2": "㉮", "c3": "㉠",
          "r1": "Ⅰ", "r2": "Ⅰ", "sq": "□", "ci": "○", "da": "-", "dt": "·"}

END_ONLY = re.compile(r"^[-=~<(\[【「―—–ㅡ*]*\.?(끝|이상)\.?[-=~>)\]】」―—–ㅡ*]*$")      # 공백을 지운 뒤 비교
END_TAIL = re.compile(r"(?:^|(?<=[\s.]))\.?\s*끝\.?$")
ATTACH = re.compile(r"^(\(\s*(?:붙임|첨부|별첨)\s*\)|(?:붙임|첨부|별첨)\s*\))|^(붙임|첨부|별첨)(?=\s|$|\d|[①-⑳]|\s*[:：])")
INLINE_AREA = re.compile(r"^(.*\S)\s+([-=~―─—–ㅡ<＜〈\[【「(]+\s*(?:아\s*래|다\s*음)\s*[-=~―─—–ㅡ>＞〉\]】」)]+)$")
INLINE_ORD = re.compile(r"(?:(?<=\s)|^)(?:([가나다라마바사아자차카타파하])\.|\(([가나다라마바사아자차카타파하])\))(?=\s)")
TITLE = re.compile(r"^제\s*목\s*[:：]")


def width(s):
    """화면에서 차지하는 칸 수 (한글 · 한자 · 전각 = 2칸)"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" or c == "○" else 1 for c in s)


def clean(s):
    """보이지 않는 글자를 지우고 특수 공백을 보통 공백으로 (전각 공백 = 2칸)"""
    s = s.translate(INVISIBLE).replace("\u00a0", " ").replace("\u3000", "  ")
    s = re.sub(r"[\u2000-\u200a\u202f\u205f]", " ", s)
    return s.rstrip()


def lead_width(s):
    lead = s[: len(s) - len(s.lstrip(" \t"))]
    return lead.count(" ") + lead.count("\t") * CFG["탭_칸수"]


def body_of(s):
    return s.lstrip(" \t").replace("\t", " " * CFG["탭_칸수"])


def note(msg):
    if msg not in NOTES:
        NOTES.append(msg)


# ── 읽기 : 파일 → 품의서 목록. 품의서 하나 = 줄(str) · 표(칸 글자 목록의 목록) 목록 ──

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
W = "{%s}" % NS["w"]


def local(el):
    return el.tag.rsplit("}", 1)[-1]


RUN_SKIP = ("pPr", "rPr", "tabs", "instrText", "delText", "fldData", "Fallback")


def runs(par):
    """문단 하나의 글자 (탭 · 줄바꿈 포함). 문단 설정(pPr)의 탭 위치 · 지운 글자는 넣지 않는다"""
    buf = []

    def walk(el):
        for ch in el:
            tag = local(ch)
            if tag in RUN_SKIP:
                continue
            if tag == "t":
                buf.append(ch.text or "")
            elif tag == "tab":
                buf.append("\t")
            elif tag in ("br", "cr"):
                buf.append("\n")
            elif tag == "noBreakHyphen":
                buf.append("-")
            else:
                walk(ch)
    walk(par)
    return "".join(buf)


def cell_text(cell):
    return " / ".join(t.strip() for t in (runs(p) for p in cell.iter() if local(p) == "p") if t.strip())


def decode(raw, name):
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", "replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if raw[:200].count(b"\x00") > 20:                                    # BOM 없는 utf-16
        return raw.decode("utf-16-le" if raw[1:2] == b"\x00" else "utf-16-be", "replace")
    for enc in ("utf-8", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    raise 읽기안내("글자 인코딩을 알 수 없습니다 — 메모장에서 「다른 이름으로 저장 → 인코딩 UTF-8」로 저장해 넣어 주세요")


def md_lines(lines):
    """md 표시 기호를 지우고 구조만 남긴다"""
    out, fence = [], False
    for l in lines:
        if re.match(r"^\s*(```|~~~)", l):
            fence = not fence
            continue
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", l)
        if m:
            if not CFG["제목줄_빼기"]:
                out.append(m.group(1).replace("**", "").replace("__", ""))
            continue
        if re.fullmatch(r"\s*([-*_]\s*){3,}", l) and not l.strip().startswith("|"):
            continue                                                     # 가로줄
        l = re.sub(r"^(\s*)>\s?", r"\1", l)
        l = re.sub(r"^(\s*)[*+]\s+", r"\1- ", l)
        l = l.replace("**", "").replace("__", "").replace("`", "")
        out.append(l)
    return out


def split_cells(s):
    return [c.strip() for c in s.split("|")]


def table_from_pipes(lines, i):
    """| 칸 | 칸 | 줄 (양끝 있음 1줄 이상) 또는 칸 | 칸 줄 (양끝 없음, 같은 칸 수 2줄 이상)"""
    s = lines[i].strip()
    if len(s) > 1 and s.startswith("|") and s.endswith("|"):
        rows, j = [], i
        while j < len(lines):
            t = lines[j].strip()
            if not (len(t) > 1 and t.startswith("|") and t.endswith("|")):
                break
            cells = split_cells(t[1:-1])
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                rows.append(cells)
            j += 1
        return (rows, j) if rows else ([], j)
    if "|" not in s or s.startswith("|"):
        return None
    n = len(split_cells(s))
    j = i
    while j < len(lines) and "|" in lines[j] and len(split_cells(lines[j].strip())) == n:
        j += 1
    if n >= 2 and j - i >= 2:
        rows = [split_cells(lines[k].strip()) for k in range(i, j)]
        return [r for r in rows if not all(re.fullmatch(r":?-{3,}:?", c) for c in r)], j
    return None


def table_from_tabs(lines, i):
    """탭으로 칸을 나눈 줄 (엑셀에서 붙여 넣은 표). 칸 3개 이상 줄이 2줄 이상, 또는 칸 2개 이상 줄이 3줄 이상"""
    def cells(l):
        b = l.strip(" ").lstrip("\t")
        return b.split("\t") if "\t" in b else None
    j = i
    while j < len(lines) and cells(lines[j]) and len(cells(lines[j])) >= 2:
        j += 1
    if j - i < 2 or (j - i < 3 and min(len(cells(lines[k])) for k in range(i, j)) < 3):
        return None
    if all(lines[k].strip(" ").startswith("\t") for k in range(i, j)):
        rows = [[c.strip() for c in cells(lines[k])] for k in range(i, j)]                  # 표 전체를 탭으로 들여 씀
    else:
        rows = [[c.strip() for c in lines[k].strip(" ").split("\t")] for k in range(i, j)]  # 탭으로 시작하는 줄 = 첫 칸이 빔
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    while n > 1 and all(not r[-1] for r in rows):                       # 끝의 빈 칸 줄
        rows = [r[:-1] for r in rows]
        n -= 1
    return rows, j


BOX_SEP = re.compile(r"^[┌┬┐├┼┤└┴┘─━═╔╦╗╠╬╣╚╩╝+\-=\s]+$")
BOX_BAR = "│┃║|"


def table_from_box(lines, i):
    """┌─┬─┐ │ 칸 │ 괘선 표"""
    s = lines[i].strip()
    if not s or not ((s[0] in "┌├└╔╠╚+" and BOX_SEP.match(s)) or s[0] in "│┃║"):
        return None
    rows, j = [], i
    while j < len(lines):
        t = lines[j].strip()
        if t and BOX_SEP.match(t) and any(c in t for c in "┌┬┐├┼┤└┴┘─━═+"):
            j += 1
            continue
        if t and t[0] in BOX_BAR and sum(t.count(c) for c in BOX_BAR) >= 2:
            rows.append([c.strip() for c in re.split(r"[│┃║|]", t.strip("│┃║|"))])
            j += 1
            continue
        break
    return (rows, j) if rows else None


def table_from_spaces(lines, i, measure=None):
    """두 칸 이상 공백으로 칸을 맞춘 줄. 첫 줄 칸 수 ≥ 공백표_최소칸, 줄 수 ≥ 공백표_최소줄, 같은 들여쓰기일 때만.
    measure = 칸 위치를 세는 법 (보통은 한글 2칸, pdf 에서 꺼낸 글은 글자 1개 = 1칸)"""
    measure = measure or width
    def tokens(l):
        body = l.lstrip(" ")
        lead = len(l) - len(body)
        out, pos = [], 0
        for m in re.finditer(r"\S+(?: \S+)*", body):
            out.append((measure(body[: m.start()]), m.group()))
        return lead, out

    def plain(l):
        b = l.strip()
        return b and "\t" not in l and not MARK.match(b.translate(FULLWIDTH)) and not AREA_FIND.match(b) \
            and not ATTACH.match(b) and re.search(r"\S {2,}\S", b)
    if not plain(lines[i]):
        return None
    lead, head = tokens(lines[i])
    if len(head) < CFG["공백표_최소칸"]:
        return None
    starts = [p for p, _ in head]
    rows, j = [[t for _, t in head]], i + 1
    while j < len(lines) and plain(lines[j]):
        l2, toks = tokens(lines[j])
        if l2 != lead:
            break
        row, used = [""] * len(starts), set()
        for p, t in toks:
            k = max((n for n, s0 in enumerate(starts) if s0 <= p + 1), default=None)
            if k is None or k in used:
                row = None
                break
            used.add(k)
            row[k] = t
        if row is None:
            break
        rows.append(row)
        j += 1
    if len(rows) < CFG["공백표_최소줄"]:
        return None
    note(f"공백으로 맞춘 줄을 표로 바꿈 ({len(starts)}칸 {len(rows)}줄)")
    return rows, j


def text_blocks(lines, measure=None):
    """글줄 목록 → 줄 · 표 목록 (글자로 쓴 표를 찾아 표로 묶는다)"""
    blocks, i = [], 0
    while i < len(lines):
        found = None
        for finder in (table_from_pipes, table_from_box, table_from_tabs, table_from_spaces):
            found = finder(lines, i, measure) if finder is table_from_spaces else finder(lines, i)
            if found:
                break
        if found:
            rows, j = found
            if rows:
                blocks.append(rows)
            i = j
            continue
        blocks.append(lines[i])
        i += 1
    return blocks


def read_text(path, md=False):
    lines = decode(path.read_bytes(), path.name).splitlines()
    if md:
        lines = md_lines(lines)
    return [text_blocks(lines)]


# docx

ROMAN_NUM = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def roman(n):
    out = ""
    for v, r in ROMAN_NUM:
        while n >= v:
            out, n = out + r, n - v
    return out


def num_text(n, fmt):
    if fmt in ("ganada",):
        return KOR[(n - 1) % len(KOR)]
    if fmt in ("chosung",):
        return "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ"[(n - 1) % 14]
    if fmt.startswith("decimalEnclosedCircle") and 1 <= n <= 20:
        return CIRC_NUM[n - 1]
    if fmt == "upperRoman":
        return roman(n)
    if fmt == "lowerRoman":
        return roman(n).lower()
    if fmt == "upperLetter":
        return chr(64 + (n - 1) % 26 + 1)
    if fmt == "lowerLetter":
        return chr(96 + (n - 1) % 26 + 1)
    return str(n)


BULLET_CHARS = {"\uf0b7": "•", "\uf0a7": "■", "\uf076": "◆", "\uf0d8": "▶", "\uf0fc": "•", "\uf06e": "■", "\uf071": "□", "o": "◦"}


def bullet_char(c):
    c = (c or "•")[:1]
    if c in BULLET_CHARS:
        return BULLET_CHARS[c]
    return "•" if "\ue000" <= c <= "\uf8ff" else c


def twips_to_spaces(v):
    return max(0, round(v / 120))                     # 12pt 글자 반 칸 ≈ 120 twips


def ind_value(ind):
    if ind is None:
        return None
    g = lambda k: int(ind.get(W + k, "0") or 0)
    left = g("left") or g("start")
    return left - g("hanging") + g("firstLine")


class Numbering:
    """docx 자동 번호 (numbering.xml) → 글자"""

    def __init__(self, z):
        self.abstract, self.nums, self.count = {}, {}, {}
        if "word/numbering.xml" not in z.namelist():
            return
        root = ET.fromstring(z.read("word/numbering.xml"))
        for an in root.findall("w:abstractNum", NS):
            levels = {}
            for lvl in an.findall("w:lvl", NS):
                g = lambda tag: (lvl.find(f"w:{tag}", NS).get(W + "val") if lvl.find(f"w:{tag}", NS) is not None else None)
                levels[int(lvl.get(W + "ilvl"))] = {
                    "fmt": g("numFmt") or "decimal", "text": g("lvlText") or "", "start": int(g("start") or 1),
                    "suff": g("suff") or "tab", "ind": ind_value(lvl.find("w:pPr/w:ind", NS))}
            self.abstract[an.get(W + "abstractNumId")] = levels
        for num in root.findall("w:num", NS):
            a = num.find("w:abstractNumId", NS)
            starts = {}
            for ov in num.findall("w:lvlOverride", NS):
                so = ov.find("w:startOverride", NS)
                if so is not None:
                    starts[int(ov.get(W + "ilvl"))] = int(so.get(W + "val"))
            self.nums[num.get(W + "numId")] = (a.get(W + "val") if a is not None else None, starts)

    def level(self, num_id, ilvl):
        a, starts = self.nums.get(num_id, (None, {}))
        lv = dict(self.abstract.get(a, {}).get(ilvl, {}))
        if lv and ilvl in starts:
            lv["start"] = starts[ilvl]
        return lv

    def marker(self, num_id, ilvl):
        lv = self.level(num_id, ilvl)
        if not lv:
            return "", None
        cnt = self.count.setdefault(num_id, [0] * 10)
        cnt[ilvl] += 1
        for k in range(ilvl + 1, 10):
            cnt[k] = 0
        if lv["fmt"] in ("bullet", "none"):
            text = bullet_char(lv["text"]) if lv["fmt"] == "bullet" else ""
        else:
            def sub(m):
                k = int(m.group(1)) - 1
                lk = self.level(num_id, k)
                n = max(cnt[k], 1) + (lk.get("start", 1) if lk else 1) - 1
                return num_text(n, lk.get("fmt", "decimal") if lk else "decimal")
            text = re.sub(r"%(\d)", sub, lv["text"])
        return (text + ("" if lv["suff"] == "nothing" else " ")) if text else "", lv["ind"]


def docx_styles(z):
    """문단 스타일 → (번호 numPr, 들여쓰기) — basedOn 을 따라간다"""
    if "word/styles.xml" not in z.namelist():
        return {}
    raw = {}
    for st in ET.fromstring(z.read("word/styles.xml")).findall("w:style", NS):
        ppr = st.find("w:pPr", NS)
        based = st.find("w:basedOn", NS)
        raw[st.get(W + "styleId")] = (ppr, based.get(W + "val") if based is not None else None)
    out = {}
    for sid in raw:
        num, ind, cur, seen = None, None, sid, set()
        while cur in raw and cur not in seen:
            seen.add(cur)
            ppr, based = raw[cur]
            if ppr is not None:
                if num is None and ppr.find("w:numPr", NS) is not None:
                    num = ppr.find("w:numPr", NS)
                if ind is None and ppr.find("w:ind", NS) is not None:
                    ind = ppr.find("w:ind", NS)
            cur = based
        out[sid] = (num, ind)
    return out


def docx_table(tbl):
    rows = []
    for tr in tbl.findall("w:tr", NS):
        row = []
        for tc in tr.findall("w:tc", NS):
            pr = tc.find("w:tcPr", NS)
            span = pr.find("w:gridSpan", NS) if pr is not None else None
            vm = pr.find("w:vMerge", NS) if pr is not None else None
            cont = vm is not None and vm.get(W + "val", "continue") != "restart"
            row.append("^^" if cont else cell_text(tc))
            row += ["<<"] * (int(span.get(W + "val")) - 1 if span is not None else 0)
        rows.append(row)
    return rows


def read_docx(z):
    styles, numbering = docx_styles(z), Numbering(z)
    blocks = []

    def walk(parent):
        for el in parent:
            tag = local(el)
            if tag == "sdt":
                content = el.find("w:sdtContent", NS)
                if content is not None:
                    walk(content)
            elif tag == "p":
                ppr = el.find("w:pPr", NS)
                sid = ppr.find("w:pStyle", NS).get(W + "val") if ppr is not None and ppr.find("w:pStyle", NS) is not None else None
                s_num, s_ind = styles.get(sid, (None, None))
                num = ppr.find("w:numPr", NS) if ppr is not None else None
                num = num if num is not None else s_num
                mark, lvl_ind = "", None
                if num is not None:
                    nid = num.find("w:numId", NS)
                    lv = num.find("w:ilvl", NS)
                    nid = nid.get(W + "val") if nid is not None else None
                    if nid and nid != "0":
                        mark, lvl_ind = numbering.marker(nid, int(lv.get(W + "val")) if lv is not None else 0)
                ind = ind_value(ppr.find("w:ind", NS)) if ppr is not None and ppr.find("w:ind", NS) is not None else None
                for v in (lvl_ind, ind_value(s_ind)):
                    ind = v if ind is None else ind
                lead = " " * twips_to_spaces(ind or 0)
                text = runs(el)
                lines = text.split("\n")
                if mark and text.strip():
                    lines[0] = mark + lines[0].lstrip()
                blocks.extend(lead + l if l.strip() else l for l in lines)
            elif tag == "tbl":
                blocks.append(docx_table(el))

    walk(ET.fromstring(z.read("word/document.xml")).find("w:body", NS))
    return [blocks]


# pptx

SKIP_PH = ("title", "ctrTitle", "subTitle", "sldNum", "ftr", "dt", "hdr")
AUTO_NUM = {"arabicPeriod": "%s.", "arabicParenR": "%s)", "arabicParenBoth": "(%s)", "arabicPlain": "%s",
            "romanUcPeriod": "R.", "romanLcPeriod": "r.", "circleNumDbPlain": "C", "circleNumWdBlackPlain": "C",
            "alphaLcParenR": "a)", "alphaUcPeriod": "A.", "alphaLcPeriod": "a.", "hangulKoreanPeriod": "K."}


def auto_number(kind, n):
    tpl = AUTO_NUM.get(kind, "%s.")
    if tpl == "R.":
        return roman(n) + "."
    if tpl == "r.":
        return roman(n).lower() + "."
    if tpl == "C":
        return CIRC_NUM[n - 1] if n <= 20 else f"{n}."
    if tpl in ("a)", "A.", "a."):
        ch = chr((96 if tpl[0] == "a" else 64) + (n - 1) % 26 + 1)
        return ch + tpl[1:]
    if tpl == "K.":
        return KOR[(n - 1) % 14] + "."
    return tpl % n


def pptx_text(tx):
    lines, counters = [], {}
    for p in tx.findall("a:p", NS):
        ppr = p.find("a:pPr", NS)
        lvl = int(ppr.get("lvl", "0")) if ppr is not None else 0
        text = runs(p)
        mark = ""
        if ppr is not None and ppr.find("a:buNone", NS) is None:
            an, bc = ppr.find("a:buAutoNum", NS), ppr.find("a:buChar", NS)
            if an is not None and text.strip():
                n = counters.get(lvl, int(an.get("startAt", "1")) - 1) + 1
                counters[lvl] = n
                for k in [k for k in counters if k > lvl]:
                    del counters[k]
                mark = auto_number(an.get("type", "arabicPeriod"), n) + " "
            elif bc is not None and text.strip():
                mark = bullet_char(bc.get("char")) + " "
        if not mark:
            for k in [k for k in counters if k > lvl]:
                del counters[k]
        parts = text.split("\n")
        if mark:
            parts[0] = mark + parts[0].lstrip()
        lead = " " * (lvl * CFG["탭_칸수"])
        lines += [lead + l if l.strip() else l for l in parts]
    return lines


def pptx_table(tbl):
    rows = []
    for tr in tbl.findall("a:tr", NS):
        row = []
        for tc in tr.findall("a:tc", NS):
            if tc.get("hMerge") == "1":
                row.append("<<")
            elif tc.get("vMerge") == "1":
                row.append("^^")
            else:
                row.append(cell_text(tc))
        rows.append(row)
    return rows


def pptx_shapes(tree, dx=0, dy=0):
    """슬라이드의 글상자 · 표 → (y, x, 자리표시 종류, 줄 또는 표)"""
    out = []
    for sp in tree:
        tag = local(sp)
        if tag == "grpSp":
            x = sp.find("p:grpSpPr/a:xfrm", NS)
            off, ch = (x.find("a:off", NS), x.find("a:chOff", NS)) if x is not None else (None, None)
            ox = int(off.get("x")) - int(ch.get("x")) if off is not None and ch is not None else 0
            oy = int(off.get("y")) - int(ch.get("y")) if off is not None and ch is not None else 0
            out += pptx_shapes(sp, dx + ox, dy + oy)
            continue
        if tag not in ("sp", "graphicFrame"):
            continue
        ph = sp.find(".//p:nvPr/p:ph", NS)
        ph_type = (ph.get("type", "body") if ph is not None else None)
        if ph_type in SKIP_PH:
            continue
        off = sp.find("p:spPr/a:xfrm/a:off", NS)
        if off is None:
            off = sp.find("p:xfrm/a:off", NS)
        y = (int(off.get("y")) if off is not None else 0) + dy
        x = (int(off.get("x")) if off is not None else 0) + dx
        tbl = sp.find(".//a:tbl", NS)
        if tbl is not None:
            out.append((y, x, ph_type, pptx_table(tbl), None))
            continue
        tx = sp.find("p:txBody", NS)
        if tx is not None:
            lines = pptx_text(tx)
            if any(l.strip() for l in lines):
                ext = sp.find("p:spPr/a:xfrm/a:ext", NS)
                cy = int(ext.get("cy")) if ext is not None and ext.get("cy") else None
                out.append((y, x, ph_type, lines, pptx_line_tops(tx, y, cy)))
    return out


def pptx_line_tops(tx, y, cy=None):
    """글상자의 줄마다 윗변 세로 위치 (글자 크기 × 줄간격으로 어림한다). pptx_text 의 줄과 하나씩 맞는다.
    어림한 높이가 글상자 실제 높이(cy)보다 크면 실제 높이에 맞게 줄인다 (글상자 아래 바깥의 표를 안으로 넣지 않게)"""
    body = tx.find("a:bodyPr", NS)
    top = y + int(body.get("tIns", "45720") if body is not None else 45720)
    tops = []
    for p in tx.findall("a:p", NS):
        sizes = [int(r.get("sz")) for r in p.iter() if local(r) in ("rPr", "endParaRPr") and r.get("sz")]
        pct = p.find("a:pPr/a:lnSpc/a:spcPct", NS)
        h = (max(sizes) if sizes else 1800) / 100 * 12700 * 1.2 * (int(pct.get("val")) / 100000 if pct is not None else 1)
        for _ in runs(p).split("\n"):
            tops.append(top)
            top += h
    if cy and top > y + cy and top > y:
        k = cy / (top - y)
        tops = [y + (v - y) * k for v in tops]
    return tops


def read_pptx(z):
    """슬라이드마다 「아래」 줄이 있는 글상자를 본문으로 보고, 그 슬라이드의 글상자 · 표를 위치 순서로 잇는다.
    본문 글상자보다 위에 있는 자리표시(제목 · 소제목 상자)는 넣지 않는다. 「아래」 줄이 있는 슬라이드가 하나도 없으면
    자리표시가 아닌 글상자가 있는 슬라이드마다 한 건으로 본다"""
    names = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                   key=lambda n: int(re.findall(r"\d+", n)[0]))
    slides = [pptx_shapes(ET.fromstring(z.read(n)).find(".//p:cSld/p:spTree", NS)) for n in names]
    docs, any_area = [], False
    for shapes in slides:
        main = next((s for s in sorted(shapes, key=lambda s: (s[0], s[1]))
                     if isinstance(s[3][0] if s[3] else None, str) and any(AREA_FIND.match(clean(l).strip()) for l in s[3])), None)
        if main is None:
            continue
        any_area = True
        keep = [s for s in shapes if s[0] >= main[0] or s[2] is None]
        docs.append(slide_blocks(keep))
    if not any_area:
        for shapes in slides:
            keep = [s for s in shapes if s[2] is None]
            if keep:
                docs.append(slide_blocks(keep))
    return docs


def slide_blocks(shapes):
    """위치 순서로 잇는다. 글상자 안 빈 자리에 겹쳐 놓은 표는 글상자 밖 뒤가 아니라 그 세로 위치의 줄 사이에 넣는다"""
    texts = [s for s in shapes if s[4] is not None]
    inside, rest = {}, []
    for s in shapes:
        host = None
        if s[4] is None:
            host = next((t for t in sorted(texts, key=lambda t: -t[0]) if t[4][0] < s[0] < t[4][-1]), None)
        if host is None:
            rest.append(s)
        else:
            inside.setdefault(id(host), []).append(s)
    blocks = []
    for s in sorted(rest, key=lambda s: (s[0], s[1])):
        data = s[3]
        if s[4] is None:
            blocks.append(data)
            continue
        lines = list(data)
        for tb in sorted(inside.get(id(s), []), key=lambda tb: -tb[0]):
            at = sum(1 for t in s[4] if t < tb[0])
            lines.insert(at, tb[3])
        blocks += lines
    return blocks


# xlsx

def xlsx_rels(z, path):
    folder, name = path.rsplit("/", 1)
    rel = f"{folder}/_rels/{name}.rels"
    if rel not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(rel)):
        t = r.get("Target")
        out[r.get("Id")] = t.lstrip("/") if t.startswith("/") else posixpath.normpath(f"{folder}/{t}").replace("\\", "/")
    return out


def col_index(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    c = 0
    for ch in m.group(1):
        c = c * 26 + ord(ch) - 64
    return int(m.group(2)), c


DATE_FMT_IDS = set(range(14, 23)) | set(range(45, 48))


def excel_number(v, fmt_id, code):
    try:
        x = float(v)
    except ValueError:
        return v
    code = code or ""
    plain = re.sub(r'"[^"]*"|\\.|\[[^\]]*\]', "", code)
    if fmt_id in DATE_FMT_IDS or (re.search(r"[yd]", plain, re.I) and not re.search(r"[#0]", plain)):
        d = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(x))
        code = re.sub(r"[hHsS]+|:|AM/PM|a{3,}|d{3,}", "", plain).strip() if plain else ""
        if not re.search(r"[ymd]", code, re.I):
            return f"{d:%Y-%m-%d}"
        parts = {"yyyy": f"{d.year}", "yy": f"{d.year % 100:02d}", "mm": f"{d.month:02d}", "m": f"{d.month}",
                 "dd": f"{d.day:02d}", "d": f"{d.day}"}
        return re.sub(r"yyyy|yy|mm|m|dd|d", lambda m: parts[m.group().lower()], code, flags=re.I).strip()
    if fmt_id in (9, 10) or "%" in plain:
        dec = 2 if fmt_id == 10 else len(re.search(r"\.(0*)", plain).group(1)) if re.search(r"\.(0*)", plain) else 0
        return f"{x * 100:.{dec}f}%"
    if fmt_id in (3, 4) or "#,##0" in plain:
        dec = 2 if fmt_id == 4 else len(re.search(r"\.(0+)", plain).group(1)) if re.search(r"\.(0+)", plain) else 0
        return f"{x:,.{dec}f}"
    if fmt_id == 2:
        return f"{x:.2f}"
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return f"{x:.10g}"


def read_xlsx(z):
    """시트 하나 = 품의서 한 건 (「아래」 줄이 있는 시트가 있으면 그 시트만)"""
    names = z.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", NS):
            parts = [t.text or "" for t in si.findall("s:t", NS)]
            parts += [t.text or "" for r in si.findall("s:r", NS) for t in r.findall("s:t", NS)]
            shared.append("".join(parts))                                # 윗주(rPh)는 넣지 않는다
    xf, fmts = [], {}
    if "xl/styles.xml" in names:
        st = ET.fromstring(z.read("xl/styles.xml"))
        for nf in st.findall("s:numFmts/s:numFmt", NS):
            fmts[int(nf.get("numFmtId"))] = nf.get("formatCode")
        xf = [int(x.get("numFmtId", "0")) for x in st.findall("s:cellXfs/s:xf", NS)]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = xlsx_rels(z, "xl/workbook.xml")
    docs, area_docs = [], []
    for sh in wb.findall("s:sheets/s:sheet", NS):
        target = rels.get(sh.get(f"{{{NS['r']}}}id"))
        if not target or target not in names:
            continue
        root = ET.fromstring(z.read(target))
        cells = {}
        for c in root.iter(f"{{{NS['s']}}}c"):
            r, col = col_index(c.get("r"))
            t, v = c.get("t"), c.find("s:v", NS)
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter() if local(x) == "t")
            elif t == "b" and v is not None:
                val = "TRUE" if v.text == "1" else "FALSE"
            elif v is not None and v.text is not None:
                s_i = int(c.get("s", "0"))
                fid = xf[s_i] if s_i < len(xf) else 0
                val = v.text if t in ("str", "e") else excel_number(v.text, fid, fmts.get(fid))
            else:
                continue
            if val.strip():
                cells[(r, col)] = val
        merged = {}
        for mc in root.findall("s:mergeCells/s:mergeCell", NS):
            a, b = mc.get("ref").split(":") if ":" in mc.get("ref") else (mc.get("ref"),) * 2
            (r1, c1), (r2, c2) = col_index(a), col_index(b)
            for rr in range(r1, r2 + 1):
                for cc in range(c1, c2 + 1):
                    if (rr, cc) != (r1, c1):
                        merged[(rr, cc)] = "<<" if rr == r1 else "^^"
        if not cells:
            continue
        blocks = sheet_blocks(cells, merged)
        docs.append(blocks)
        if any(isinstance(b, str) and AREA_FIND.match(clean(b).strip()) for b in blocks):
            area_docs.append(blocks)
    return area_docs or docs


def sheet_blocks(cells, merged):
    rows = sorted({r for r, _ in cells})
    min_c = min(c for _, c in cells)
    blocks, group = [], []

    def flush():
        if not group:
            return
        if len(group) == 1:
            r = group[0]
            blocks.append("  ".join(cells[(r, c)] for c in sorted(c for rr, c in cells if rr == r)))
        else:
            c1 = min(c for rr, c in cells if rr in group)
            c2 = max(c for rr, c in cells if rr in group)
            table = []
            for r in group:
                table.append([cells.get((r, c), merged.get((r, c), "")) for c in range(c1, c2 + 1)])
            blocks.append(table)
        group.clear()

    prev = None
    for r in rows:
        if prev is not None and r > prev + 1:
            flush()
            blocks.append("")
        filled = sorted(c for rr, c in cells if rr == r)
        if len(filled) >= 2:
            group.append(r)
        else:
            flush()
            blocks.append(" " * ((filled[0] - min_c) * CFG["탭_칸수"]) + cells[(r, filled[0])])
        prev = r
    flush()
    return blocks


# pdf

def read_pdf(path):
    if str(LIB) not in sys.path:
        sys.path.insert(0, str(LIB))
    try:
        import pypdf
    except ImportError:
        raise 읽기안내("PDF를 읽는 부품(프로그램\\lib\\pypdf)이 없습니다 — 원본 문서(docx 등)로 넣어 주세요")
    try:
        reader = pypdf.PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt("")
        pages = [p.extract_text(extraction_mode="layout") or "" for p in reader.pages]
    except Exception:
        raise 읽기안내("PDF를 열지 못했습니다 — 원본 문서(docx 등)로 넣어 주세요")
    if not any(re.search(r"[가-힣A-Za-z0-9]", p) for p in pages):
        raise 읽기안내("글자를 읽을 수 없는 PDF입니다 — 원본 문서로 넣어 주세요")
    lines = []
    for p in pages:
        pl = [l.rstrip() for l in p.splitlines()]
        lead = min((len(l) - len(l.lstrip(" ")) for l in pl if l.strip()), default=0)   # 쪽 여백은 뺀다
        lines += [l[lead:] for l in pl]
    return [text_blocks(lines, measure=len)]


# hwpx

def hwpx_table(tbl):
    grid = {}
    for tr in [x for x in tbl if local(x) == "tr"]:
        for tc in [x for x in tr if local(x) == "tc"]:
            addr = next((x for x in tc if local(x) == "cellAddr"), None)
            span = next((x for x in tc if local(x) == "cellSpan"), None)
            r, c = (int(addr.get("rowAddr")), int(addr.get("colAddr"))) if addr is not None else (len(grid), 0)
            rs, cs = (int(span.get("rowSpan", "1")), int(span.get("colSpan", "1"))) if span is not None else (1, 1)
            grid[(r, c)] = " / ".join(t for t in (hwpx_par_text(p).strip() for p in tc.iter() if local(p) == "p") if t)
            for rr in range(r, r + rs):
                for cc in range(c, c + cs):
                    if (rr, cc) != (r, c):
                        grid[(rr, cc)] = "<<" if rr == r else "^^"
    if not grid:
        return []
    nr, nc = max(r for r, _ in grid) + 1, max(c for _, c in grid) + 1
    return [[grid.get((r, c), "") for c in range(nc)] for r in range(nr)]


def hwpx_par_text(p):
    buf = []
    for run in [x for x in p if local(x) == "run"]:
        for el in run:
            if local(el) == "t":
                buf.append(el.text or "")
                for ch in el:
                    buf.append("\t" if local(ch) == "tab" else "\n" if local(ch) == "lineBreak" else "")
                    buf.append(ch.tail or "")
    return "".join(buf)


def read_hwpx(z):
    names = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                   key=lambda n: int(re.findall(r"\d+", n)[0]))
    if not names:
        raise 읽기안내("한글(hwpx) 본문을 찾지 못했습니다 — 한글에서 docx로 저장해 넣어 주세요")
    blocks = []
    for n in names:
        for p in ET.fromstring(z.read(n)):
            if local(p) != "p":
                continue
            line = []
            for run in [x for x in p if local(x) == "run"]:
                for el in run:
                    if local(el) == "t":
                        line.append(el.text or "")
                        for ch in el:
                            line.append("\t" if local(ch) == "tab" else "\n" if local(ch) == "lineBreak" else "")
                            line.append(ch.tail or "")
                    elif local(el) == "tbl":
                        if "".join(line).strip():
                            blocks += "".join(line).split("\n")
                        line = []
                        blocks.append(hwpx_table(el))
            blocks += "".join(line).split("\n")
    return [[b for b in blocks if b != []]]


# rtf

RTF_SKIP = ("fonttbl", "colortbl", "stylesheet", "info", "pict", "header", "footer", "listtable", "listoverridetable",
            "rsidtbl", "generator", "themedata", "colorschememapping", "latentstyles", "datastore", "xmlnstbl", "mmathPr")


def read_rtf(path):
    """rtf → 글줄. 표(\\cell · \\row)는 | 칸 | 칸 | 줄로 바꿔 표로 읽는다"""
    data = path.read_bytes().decode("latin-1")
    m = re.search(r"\\ansicpg(\d+)", data)
    cp = f"cp{m.group(1)}" if m else "cp949"
    try:
        "".encode(cp)
    except LookupError:
        cp = "cp949"
    text, cur, cell_parts, row = [], [], [], []
    stack, skip, uc, intbl, pend = [], False, 1, False, bytearray()
    token = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-fA-F]{2})|\\(.)|([{}])|([^\\{}\r\n]+)|[\r\n]+", re.S)

    def flush():
        if pend:
            cur.append(pend.decode(cp, "replace"))
            pend.clear()

    pos, skip_chars = 0, 0
    while pos < len(data):
        t = token.match(data, pos)
        if not t:
            pos += 1
            continue
        pos = t.end()
        word, arg, hexv, sym, brace, plain = t.groups()
        if skip_chars and (hexv or plain):                              # \u 다음의 대체 글자는 건너뛴다
            if plain:
                n = min(skip_chars, len(plain))
                plain, skip_chars = plain[n:], skip_chars - n
            else:
                skip_chars -= 1
                continue
        if hexv:
            if not skip:
                pend.append(int(hexv, 16))
            continue
        flush()
        if brace == "{":
            stack.append(skip)
            if data.startswith("\\*", pos):
                skip = True
        elif brace == "}":
            skip = stack.pop() if stack else False
        elif sym:
            if not skip and sym in "\\{}":
                cur.append(sym)
            elif not skip and sym == "~":
                cur.append(" ")
        elif word:
            if word in RTF_SKIP:
                skip = True
            elif skip:
                pass
            elif word == "uc":
                uc = int(arg or 1)
            elif word == "u":
                n = int(arg)
                cur.append(chr(n + 65536 if n < 0 else n))
                skip_chars = uc
            elif word == "pard":
                intbl = False
            elif word == "intbl":
                intbl = True
            elif word in ("par", "line"):
                (cell_parts if intbl else text).append("".join(cur))
                cur.clear()
            elif word == "tab":
                cur.append("\t")
            elif word == "cell":
                row.append(" / ".join(x.strip() for x in cell_parts + ["".join(cur)] if x.strip()))
                cell_parts.clear()
                cur.clear()
            elif word == "row":
                if row:
                    text.append("| " + " | ".join(c.replace("|", "/") for c in row) + " |")
                row.clear()
                cur.clear()
        elif plain and not skip:
            cur.append(plain)
    flush()
    if "".join(cur).strip():
        text.append("".join(cur))
    return [text_blocks(text)]


# 옛 형식 (doc · ppt · xls · hwp) : 이 PC의 Office · 한글로 잠깐 바꿔 읽는다

OLD = {".doc": ("Word", "docx"), ".ppt": ("PowerPoint", "pptx"), ".xls": ("Excel", "xlsx"), ".hwp": ("한글", "hwpx")}


def read(path):
    """파일 → 품의서 목록 (읽지 못하면 읽기안내)"""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in PICTURES:
        raise 읽기안내("그림 파일은 글자를 읽지 못합니다 — 건너뜁니다")
    if ext in (".txt", ".md"):
        return read_text(path, md=ext == ".md")
    if ext == ".pdf":
        return read_pdf(path)
    if ext == ".rtf":
        return read_rtf(path)
    if ext in OLD:
        app, new = OLD[ext]
        raise 읽기안내(f"옛 {ext[1:]} 형식입니다 — {app}에서 열어 「다른 이름으로 저장」 → {new} 로 저장해 넣어 주세요")
    readers = {".pptx": read_pptx, ".docx": read_docx, ".xlsx": read_xlsx, ".hwpx": read_hwpx}
    if ext not in readers:
        raise 읽기안내(f"지원하지 않는 형식입니다 ({ext or '확장자 없음'}) — txt · md · docx · pptx · xlsx · pdf · hwpx 로 넣어 주세요")
    try:
        with zipfile.ZipFile(path) as z:
            return readers[ext](z)
    except zipfile.BadZipFile:
        raise 읽기안내("파일이 깨졌거나 암호가 걸려 있습니다 — 암호를 풀고 다시 저장해 넣어 주세요")


# ── 모양 맞추기 : 줄 · 표 → Guide 모양 ──

def mark_of(body):
    """줄 앞 번호 · 기호 → (계열, 값, 기호 뒤 글자) 또는 None"""
    fw = body.translate(FULLWIDTH)
    m = MARK.match(fw)
    if not m:
        return None
    g = m.lastgroup
    rest = body[m.end():]
    if not rest.strip():
        return None                                     # 기호만 있는 줄 (---- 등)
    if g == "n1" and re.match(r"\s*\d{1,2}\.", rest):
        return None                                     # 11. 6. 같은 날짜
    v = m.group(g)
    val = {"n1": lambda: int(v), "n2": lambda: int(v), "n3": lambda: int(v), "k1": lambda: KOR.index(v) + 1,
           "k2": lambda: KOR.index(v) + 1, "k3": lambda: KOR.index(v) + 1, "c1": lambda: CIRC_NUM.index(v) + 1,
           "c2": lambda: CIRC_KOR.index(v) + 1, "c3": lambda: CIRC_JAMO.index(v) + 1,
           "r1": lambda: ROMAN_U.index(v) + 1, "r2": lambda: ROMAN_A.index(v) + 1}.get(g, lambda: None)()
    return FAMILY[g], val, rest.lstrip(" \t")


def split_inline(s):
    """서두 끝에 붙은 「아래」 · 한 줄에 쓴 가. 나. 다. 를 줄로 나눈다"""
    body = s.lstrip(" \t")
    lead = s[: len(s) - len(body)]
    m = INLINE_AREA.match(body)
    if m and not AREA_FIND.match(body):
        return [lead + m.group(1), m.group(2)]
    found = [(x.start(), KOR.index(x.group(1) or x.group(2)), bool(x.group(1))) for x in INLINE_ORD.finditer(body)]
    for kind in (True, False):                                   # 가. 나. / (가) (나) — 같은 모양이 순번으로 이어질 때만
        chain = []
        for pos, n, k in found:
            if k == kind and (not chain or n == chain[-1][1] + 1):
                chain.append((pos, n))
        cuts = [p for p, _ in chain if p > 0]
        if len(chain) < 2 or not cuts:
            continue
        note("한 줄에 쓴 하위 항목을 줄로 나눔")
        parts, prev = [], 0
        for c in cuts:
            parts.append(body[prev:c].rstrip())
            prev = c
        parts.append(body[prev:].rstrip())
        child = lead + (" " if chain[0][0] > 0 else "")          # 윗 항목 글이 앞에 있으면 한 단계 아래
        return [lead + parts[0]] + [child + p for p in parts[1:]]
    return [s]


def classify(s):
    body = body_of(s)
    w = lead_width(s)
    if not body:
        return {"k": "blank"}
    if AREA_FIND.match(body):
        return {"k": "area", "w": w}
    if END_ONLY.match(re.sub(r"\s", "", body)):
        return {"k": "end", "w": w}
    if ATTACH.match(body):
        return {"k": "attach", "w": w, "body": body}
    m = mark_of(body)
    if m:
        fam, val, rest = m
        return {"k": "item", "w": w, "fam": fam, "val": val, "rest": rest, "body": body}
    return {"k": "text", "w": w, "body": body}


def cut_end(body, strict):
    """줄 끝의 끝 표시를 떼어 낸다 → (남은 글자, 뗐는가). strict = 끝 앞에 . 이 있을 때만 (중간 줄)"""
    m = END_TAIL.search(body)
    if not m or m.start() == 0:
        return body, False
    before = body[: m.start()].rstrip()
    if strict and not (before.endswith(".") or m.group().rstrip().endswith(".")):
        return body, False
    return before, True


def mark_text(fam, n):
    """계열 · 값 → 원문에 쓰였을 번호 글자 (윗 줄 안에 쓴 번호를 찾을 때)"""
    pick = lambda chars: chars[n - 1] if 1 <= n <= len(chars) else ""
    return {"1.": f"{n}.", "1)": f"{n})", "(1)": f"({n})", "가.": pick(KOR) + ".", "가)": pick(KOR) + ")",
            "(가)": f"({pick(KOR)})", "①": pick(CIRC_NUM), "㉮": pick(CIRC_KOR), "㉠": pick(CIRC_JAMO)}.get(fam, "")


def depth_of(stack, L):
    """원문 기호의 깊이를 정한다. stack = 지금 열린 단계 [{fam, w, n, mark}]"""
    fam, w = L["fam"], L["w"]
    same = [i for i, e in enumerate(stack) if e["fam"] == fam]
    if same:
        fit = [i for i in same if stack[i]["w"] <= w + 1]
        pos = fit[-1] if fit else same[0]
        deeper = pos == len(stack) - 1 and w > stack[pos]["w"] + 1
        if deeper and (fam in BULLETS or L["val"] == 1):
            pos = None                                  # 같은 기호를 더 깊게 (번호는 1부터 다시) = 한 단계 아래
        if pos is not None:
            del stack[pos + 1:]
            e = stack[pos]
            if L["val"] is not None and e["n"] is not None and L["val"] not in (e["n"] + 1, e["n"]):
                note(f"번호가 이어지지 않음 ({pos + 1}단계 {e['n']} 다음 {L['val']}) — 번호 값은 그대로 둠")
            e["n"] = L["val"] if L["val"] is not None else e["n"] + 1
            return pos + 1
    while stack and stack[-1]["fam"] in BULLETS and stack[-1]["w"] >= w:
        stack.pop()
    stack.append({"fam": fam, "w": w, "n": L["val"] if L["val"] is not None else 1})
    return len(stack)


def target_mark(stack, depth):
    e = stack[depth - 1]
    parent = stack[depth - 2]["mark"] if depth > 1 else None
    shapes = CFG["번호_모양"]
    if e["fam"] == "-" and CFG["하이픈_그대로"]:
        mark = "·" if parent == "-" else "-"
    elif e["fam"] == "·":
        mark = "·"
    else:
        tpl = shapes[min(depth, len(shapes)) - 1]
        n = e["n"]
        if "1" in tpl:
            mark = tpl.replace("1", str(n), 1)
        elif "가" in tpl:
            mark = tpl.replace("가", KOR[n - 1] if 1 <= n <= len(KOR) else str(n), 1)
        else:
            mark = "·" if tpl == "-" and parent == "-" else tpl
    e["mark"] = mark
    return mark


def indent(depth):
    ind = CFG["깊이별_앞공백"]
    return ind[depth - 1] if depth <= len(ind) else ind[-1] + 3 * (depth - len(ind))


def shape(blocks):
    """줄 · 표 목록 → [("p", 앞공백, 글자) | ("blank",) | ("area",) | ("table", 칸)]"""
    lines = []
    for b in blocks:
        if isinstance(b, list):
            if any(any(c.strip() for c in r) for r in b):
                lines.append({"k": "table", "rows": b})
            continue
        for s in split_inline(clean(b)):
            L = classify(s)
            if CFG["제목줄_빼기"] and L["k"] == "text" and TITLE.match(L["body"]):
                continue
            lines.append(L)

    # 끝 : 처음 나온 끝 표시에서 본문을 끊는다
    end_at, standalone = None, False
    for i, L in enumerate(lines):
        if L["k"] == "end":
            end_at, standalone = i, True
            break
        if L["k"] in ("text", "item", "attach"):
            new, cut = cut_end(L["body"], strict=True)
            if cut:
                L["body"], end_at = new, i
                if L["k"] == "item":
                    L["rest"] = cut_end(L["rest"], strict=False)[0]
                break
    if end_at is not None:
        left = [L for L in lines[end_at + 1:] if L["k"] != "blank"]
        if left:
            note(f"끝 표시 뒤의 {len(left)}줄은 넣지 않음")
        lines = lines[:end_at] if standalone else lines[:end_at + 1]
    else:
        last = next((L for L in reversed(lines) if L["k"] != "blank"), None)
        if last and last["k"] in ("text", "item", "attach"):
            last["body"], cut = cut_end(last["body"], strict=False)
            if cut and last["k"] == "item":
                last["rest"] = cut_end(last["rest"], strict=False)[0]
            end_at = 0 if cut else None
    need_end = end_at is not None or CFG["끝_없으면_넣기"]
    last_body = ""
    for L in lines:                                     # 바로 윗 글줄 (표 · 빈 줄은 건너뛴다)
        if L["k"] == "table":
            last_body = ""
        elif L["k"] != "blank":
            L["prev"], last_body = last_body, L.get("body", "")

    kv = lambda L: L["k"] == "item" and L["fam"] in BULLETS and re.match(r"^[^:：]{1,30}[:：]\s*\S", L["rest"])
    for a, L, b in zip(lines, lines[1:], lines[2:]):    # 「항목 : 값」 - 줄 사이에서 한 줄만 들여쓰기가 다르면 앞뒤 줄에 맞춘다
        if kv(a) and kv(L) and kv(b) and a["fam"] == L["fam"] == b["fam"] and a["w"] == b["w"] != L["w"] \
                and abs(L["w"] - a["w"]) <= 3:                   # 4칸 이상 차이는 일부러 한 단계 내린 것일 수 있어 그대로 둔다
            L["w"] = a["w"]
            note("같은 기호 줄 사이에서 들여쓰기만 다른 줄을 같은 단계로 맞춤")

    body_lines = [L for L in lines if L["k"] in ("text", "item", "attach")]
    flat = len(body_lines) >= 5 and sum(L["w"] == 0 for L in body_lines) >= 0.9 * len(body_lines)
    if flat:
        note("들여쓰기가 없는 품의서 — 번호 · 기호로 단계를 정함")

    out, stack = [], []
    phase, attach_col, has_area, table_ind = "head", None, False, indent(1)
    item_depth, after_blank = None, True                # 바로 앞 번호 줄의 깊이 · 그 뒤에 빈 줄이 있었는가
    last_k, label_col = None, None                      # 바로 앞 글줄의 종류 · [첨 부] 같은 괄호 이름 뒤 글자 위치

    def blank():
        if out and out[-1][0] != "blank":
            out.append(("blank",))

    for L in lines:
        k = L["k"]
        if k == "blank":
            after_blank = True
            continue
        was_blank, after_blank = after_blank, False
        pk, last_k = last_k, k
        if k == "area":
            blank()
            out.append(("area",))
            out.append(("blank",))
            stack.clear()
            phase, attach_col, has_area, item_depth = "body", None, True, None
            continue
        if k == "table":
            out.append(("table", L["rows"]))
            continue
        if attach_col is not None:                                         # 붙임 다음 줄 = 붙임 번호 위치
            out.append(("p", attach_col, L.get("body", "")))
            continue
        if k == "attach":
            blank()
            body = L["body"]
            m = re.match(r"^(붙임|첨부|별첨)\s+(?=\S)", body)
            if m and not re.match(r"^(붙임|첨부|별첨)\s*[:：]", body):
                body = m.group(1) + " " * CFG["붙임_뒤_공백"] + body[m.end():]
            head = re.match(r"^(\(?\s*(?:붙임|첨부|별첨)\s*\)?\s*[:：]?\s*)", body)
            attach_col = indent(1) + width(head.group(1))
            out.append(("p", indent(1), body, attach_col))
            phase, table_ind, item_depth = "body", indent(1), None
            continue
        inline = k == "item" and L["val"] and L["val"] > 1 and all(e["fam"] != L["fam"] for e in stack)
        if inline and L.get("prev") and mark_text(L["fam"], L["val"] - 1) in L["prev"]:
            before = mark_text(L["fam"], L["val"] - 1)  # 윗 줄 안에 쓴 ① 다음 줄의 ② = 윗 줄의 이어짐
            if out and out[-1][0] == "p" and before in out[-1][2]:
                col = out[-1][1] + width(out[-1][2][: out[-1][2].index(before)])
                out.append(("p", col, L["body"], col + width(before) + 1))   # 윗 줄의 ① 과 같은 위치에서 시작
                continue
            k = "text"
        if k == "item":
            if phase == "head":
                if out and CFG["아래줄_없으면_넣기"] and not has_area:
                    blank()
                    out.append(("area",))
                blank()
                phase = "body"
            depth = depth_of(stack, L)
            mark = target_mark(stack, depth)
            if depth == 1 and mark[:1].isdigit():
                blank()
            out.append(("p", indent(depth), (mark + " " + L["rest"]).rstrip(), indent(depth + 1)))
            table_ind = indent(depth + 1)
            item_depth = depth
            continue
        if phase == "head":                                                 # 서두
            out.append(("p", indent(1), L["body"]))
            continue
        if flat:                                                            # 들여쓰기가 없는 품의서의 번호 없는 줄
            if not was_blank and pk == "item" and item_depth and item_depth > 1 and L["body"].startswith("("):
                out.append(("p", indent(item_depth + 1), L["body"]))       # 가. 줄 바로 다음 ( 덧붙임 = 그 항목 글자 위치
                continue
            if not was_blank and pk == "text" and label_col is not None:    # [첨 부] 줄 다음 = 괄호 이름 뒤 글자 위치
                out.append(("p", label_col, L["body"]))
                continue
            m = re.match(r"^\[[^\]]{1,10}\]\s*", L["body"])
            label_col = None
            if stack and m:                                                 # [첨 부] 줄 = 마지막 번호(가. 1. 등) 단계 (빈 줄이 없어도)
                d = next((i + 1 for i in range(len(stack) - 1, -1, -1) if stack[i]["fam"] not in BULLETS), 1)
                label_col = indent(d) + width(m.group())
                out.append(("p", indent(d), L["body"]))
                continue
        fit = [i for i, e in enumerate(stack) if e["w"] <= L["w"]]          # 번호 없는 줄
        iw = stack[item_depth - 1]["w"] if item_depth and item_depth <= len(stack) else None
        if (iw is not None and not was_blank and (L["w"] <= iw if item_depth == 1 else
                                                  L["w"] < iw and not L.get("prev", "").rstrip().endswith("."))):
            out.append(("p", indent(item_depth + 1), L["body"]))           # 번호 줄 바로 다음 = 그 항목의 이어짐 (덜 들여 써도)
            continue
        if not fit:
            ind = indent(1)
        elif L["w"] > stack[fit[-1]]["w"]:
            ind = indent(fit[-1] + 2)                                       # 윗 항목의 이어짐 = 윗 항목 글자 위치
        else:
            ind = indent(fit[-1] + 1)                                       # 윗 항목과 같은 단계
        out.append(("p", ind, L["body"]))

    while out and out[-1][0] == "blank":
        out.pop()
    j = len(out)                                        # 본문 맨 끝의 * · ※ 덧붙임 줄은 위에 빈 줄 하나를 둔다
    while j > 0 and out[j - 1][0] == "p" and out[j - 1][2].lstrip().startswith(("*", "※")):
        j -= 1
    if 1 < j < len(out) and out[j - 1][0] == "p" and phase == "body":
        out.insert(j, ("blank",))
    if need_end and out:
        if standalone and not CFG["끝_따로줄이면_붙이기"]:
            out.append(("p", indent(1), "끝."))
        elif out[-1][0] == "p":
            kind, ind, text, *hang = out[-1]
            out[-1] = (kind, ind, text.rstrip() + " " * CFG["끝_앞공백"] + "끝.", *hang)
        else:
            out.append(("p", table_ind, "끝."))
    return out


# ── HTML 만들기 ──

def p_open():
    return f'<p style="{CFG["문단_스타일"]}">' if CFG["문단_스타일"] else "<p>"


def blank_line():
    return p_open() + ("<br>" if CFG["문단_스타일"] else "&nbsp;") + "</p>"


def p_line(lead, text):
    text = text.replace("\t", " " * CFG["탭_칸수"]).rstrip()
    body = html.escape(text)
    body = re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group()), body)       # 두 칸 이상 공백
    return f"{p_open()}{'&nbsp;' * lead}{body}</p>"


NARROW = {".": .29, ",": .29, ":": .29, ";": .29, "'": .29, "|": .29, "!": .34, "(": .36, ")": .36, "[": .36, "]": .36,
          "{": .36, "}": .36, "-": .37, "/": .43, "\\": .43, '"': .5, "*": .5, "?": .51, "&": .73, "%": .99, "@": 1.02}


SPACE = .304                                                # 공백(&nbsp;) 폭. 브라우저 실측 : 본고딕 &nbsp; 0.28em ÷ 한글 0.92em


def shown(s):
    """본고딕 12pt 로 보이는 폭 (한글 한 글자 = 1). 가린 글자 ○ 도 한글과 같게 센다"""
    w = 0
    for c in s:
        if c in " \u00a0":
            w += SPACE
        elif "가" <= c <= "힣" or "ㄱ" <= c <= "ㆎ" or c == "○":
            w += 1
        elif c.isascii():
            w += NARROW.get(c, .6 if not c.isalpha() else .7 if c.isupper() else .58)
        elif c == "·":
            w += .61
        elif unicodedata.east_asian_width(c) in "WFA":
            w += 1.09
        else:
            w += .6
    return w


def fold(lead, text, hang):
    """전자결재 한 줄 폭을 넘는 줄을 띄어쓰기 자리에서 나눈다 → [(앞공백, 글자)]. 나눈 다음 줄은 hang 위치"""
    limit = CFG["한줄_최대폭"]
    if not limit or hang * SPACE > limit / 2:
        hang = lead
    out = []
    while limit and shown(" " * lead + text) > limit:
        room, cut = limit - lead * SPACE, 0
        while cut < len(text) and shown(text[:cut + 1]) <= room:
            cut += 1
        space = text.rfind(" ", 0, cut + 1)
        if space > 0 and shown(text[:space]) >= room * .6:
            cut = space
        if cut <= 0:
            break
        head, text = text[:cut].rstrip(), text[cut:].lstrip()
        out.append((lead, head))
        lead = hang
        if not text:
            return out
    return out + [(lead, text)]


def table(rows):
    """표. 칸 글자가 << 면 왼쪽 칸과, ^^ 면 위 칸과 합친다"""
    n = max(len(r) for r in rows)
    rows = [list(r) + [""] * (n - len(r)) for r in rows]
    out = [f'<table border="1" style="{CFG["표_스타일"]}">']
    for i, r in enumerate(rows):
        tag = "th" if i == 0 else "td"
        cells = []
        for j, c in enumerate(r):
            if c in ("<<", "^^"):
                continue
            cs = 1
            while j + cs < n and r[j + cs] == "<<":
                cs += 1
            rs = 1
            while i + rs < len(rows) and rows[i + rs][j] == "^^":
                rs += 1
            span = (f' colspan="{cs}"' if cs > 1 else "") + (f' rowspan="{rs}"' if rs > 1 else "")
            style = CFG.get("머리칸_스타일", CFG["칸_스타일"]) if tag == "th" else CFG["칸_스타일"]
            cells.append(f'<{tag}{span} style="{style}">{html.escape(c)}</{tag}>')
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</table>")
    return "".join(out)


UNIT_LINE = re.compile(r"^(?:[(（][^()（）]{1,24}[:：][^()（）]{0,24}[)）]|단\s*위\s*[:：].{0,20})$")   # (단위 : 원) · 단위 : 천원
PX = 14.72                                                  # 본고딕 12pt 한글 한 글자 = 14.72px (브라우저 실측 0.92em)


def table_px(rows):
    """표가 차지할 폭(px) 어림 : 칸마다 가장 긴 글자 + 칸 여백(좌우 8px) + 테두리. 한 줄 폭을 넘으면 한 줄 폭"""
    n = max(len(r) for r in rows)
    cols = [0.0] * n
    for r in rows:
        for j, c in enumerate(list(r) + [""] * (n - len(r))):
            if c in ("<<", "^^"):
                continue
            span = 1
            while j + span < n and j + span < len(r) and r[j + span] == "<<":
                span += 1
            if span == 1:
                cols[j] = max(cols[j], shown(c) * PX)
    m = re.search(r"margin-left:\s*(\d+)px", CFG["표_스타일"])
    left = int(m.group(1)) if m else 0
    w = sum(cols) + 16 * n + (n + 1)                        # 칸 여백 좌우 8px · 테두리 1px
    room = CFG["한줄_최대폭"] * PX - left if CFG["한줄_최대폭"] else w
    return left, min(w, room)


def unit_lead(text, tbl, lead):
    """표 위 단위 줄의 앞 공백 칸 수 : 글자 끝이 표 오른쪽 끝에 오도록 (한 줄 폭은 넘지 않게)"""
    left, w = table_px(tbl)
    space = shown(" ") * PX
    need = int((left + w - 2 - shown(text) * PX) / space)        # 넘치지 않게 내림
    if CFG["한줄_최대폭"]:
        need = min(need, int((CFG["한줄_최대폭"] - shown(text)) / shown(" ")))
    return max(lead, need)


def rows(blocks):
    """품의서 본문 HTML 줄 목록 → [(줄번호, html 한 줄)]. 품의서 확인 창 · 도구\\줄번호.py 가 쓴다.
    빈 줄 · 「아래」 줄 · 표도 한 줄로 센다. 한 줄 폭을 넘어 나눈 줄은 윗 줄과 같은 줄이라 번호를 None 으로 둔다"""
    out = []

    def add(*lines):
        n = sum(1 for k, _ in out if k) + 1
        out.extend((n if i == 0 else None, h) for i, h in enumerate(lines))
    if CFG["맨위_빈줄"]:
        add(blank_line())
    items = shape(blocks)
    for i, item in enumerate(items):
        nxt = items[i + 1] if i + 1 < len(items) else None
        if item[0] == "p" and nxt and nxt[0] == "table" and UNIT_LINE.match(item[2].strip()):
            add(p_line(unit_lead(item[2].strip(), nxt[1], item[1]), item[2].strip()))   # 표 오른쪽 끝에 맞춘 단위 줄
            continue
        if item[0] == "blank":
            add(blank_line())
        elif item[0] == "area":
            add(p_line(0, AREA_LINE))
        elif item[0] == "table":
            add(table(item[1]))
        else:
            lead, text = item[1], item[2]
            add(*[p_line(a, b) for a, b in fold(lead, text, item[3] if len(item) > 3 else lead)])
    return out


def body(blocks):
    """전자결재 HTML 편집 화면에 붙여넣을 본문 (줄번호 없음)"""
    return "\n".join(h for _, h in rows(blocks))


def to_html(blocks):
    head = '<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<title>품의서 본문</title>\n</head>\n<body>\n'
    return head + body(blocks) + "\n</body>\n</html>\n"


def visible(h):
    """html 한 줄 → 보이는 글자 줄 목록 (표는 칸 줄마다 [표] 칸 | 칸)"""
    if h.lstrip().startswith("<table"):
        out = []
        for tr in re.findall(r"<tr>(.*?)</tr>", h, flags=re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S)]
            out.append("[표] " + " | ".join(cells))
        return out or ["[표]"]
    return [html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "", h))).replace("\u00a0", " ")]


def numbered(rows):
    """[(줄번호, html)] → 「  12 | 글자」 줄들 (결과 페이지와 같은 줄번호)"""
    out = []
    for n, h in rows:
        for i, line in enumerate(visible(h)):
            out.append(f"{n:>4} | {line}" if n and i == 0 else f"     | {line}")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    try:
        docs = read(Path(sys.argv[1]))
    except 읽기안내 as e:
        print(f"읽지 못함 : {e}")
        return
    for i, blocks in enumerate(docs, 1):
        if len(docs) > 1:
            print(f"── 품의서{i} ──")
        print(numbered(rows(blocks)))
        if NOTES:
            print("알림 : " + " · ".join(NOTES))
            NOTES.clear()


if __name__ == "__main__":
    main()
