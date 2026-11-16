# -*- coding: utf-8 -*-
"""원본(변환 프로그램이 읽은 줄 · 표)과 결과 HTML 을 글자 내용으로 맞대어 본다. 실행.py 가 결과 페이지 · 가린 샘플 줄번호에 쓴다.

공백 · 번호 기호 · 「아래」 줄 · 끝 표시 · 마침표는 변환 프로그램이 일부러 바꾸므로 보지 않는다.
결과에서 빠지거나 바뀐 글자가 있는 줄을 노랗게 칠할 수 있게 알려 준다. 자리만 옮겨진 내용은 칠하지 않는다
(pptx · docx 의 따로 놓인 표 · 글상자는 읽는 순서가 화면 순서와 달라 원본 쪽 자리를 믿을 수 없다).
"""
import difflib
import html
import re

ORD = re.compile(r"^(?:[\d０-９]{1,2}[.．)）]|[가나다라마바사아자차카타파하][.．)）]|[(（][\d０-９]{1,2}[)）]|[(（][가나다라마바사아자차카타파하][)）]"
                 r"|[①-⑳㉮-㉻㉠-㉭]|[Ⅰ-Ⅹ]\.?|(?:VIII|VII|VI|IV|IX|III|II|I|V|X)\.(?=\s)"
                 r"|[-–—‐‑－―ㅡ−](?:\s*\.)?|[*·•∙ㆍ‧※□■◆▶◼▪○◇▷●◦]|ㅇ(?=\s))\s*")
INLINE_ORD = re.compile(r"(?:(?<=\s)|^)(?:[가나다라마바사아자차카타파하]\.|[(（][가나다라마바사아자차카타파하][)）])(?=\s)")
END = re.compile(r"[\s\-=~―—–ㅡ*]*(?:[(\[【「<]\s*)?\.?(?:끝|이상)\s*[.)\]】」>\-=~―—–ㅡ*]*\s*$")
INLINE_AREA = re.compile(r"\s+[-=~―─—–ㅡ<＜〈\[【「(]+\s*(?:아\s*래|다\s*음)\s*[-=~―─—–ㅡ>＞〉\]】」)]+$")
AREA = re.compile(r"^[-=~_―─—–ㅡ<＜〈《\[【「(（*\s]*(?:아\s*래|다\s*음)[-=~_―─—–ㅡ>＞〉》\]】」)）*\s]*$")


def visible(h):
    """html 한 줄 → 보이는 글자 줄 목록 (표는 칸 줄마다 [표] 칸 | 칸)"""
    if h.lstrip().startswith("<table"):
        out = []
        for tr in re.findall(r"<tr>(.*?)</tr>", h, flags=re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S)]
            out.append("[표] " + " | ".join(cells))
        return out or ["[표]"]
    return [html.unescape(re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "", h))).replace(" ", " ")]


def logical(rows):
    """[(줄번호, html)] → [(줄번호, [html, …])] (한 줄 폭을 넘어 나눈 줄은 한 줄로 묶는다)"""
    out = []
    for n, h in rows:
        if n or not out:
            out.append((n or len(out) + 1, [h]))
        else:
            out[-1][1].append(h)
    return out


def content(text, table=False):
    t = text.replace(" ", " ").replace("\t", " ").strip()
    if not table:
        if AREA.match(t):
            return []
        t = END.sub("", INLINE_ORD.sub(" ", ORD.sub("", INLINE_AREA.sub("", t), count=1)))
    return [c for c in t if not c.isspace() and c not in ".．"]


def compare(blocks, rows):
    """→ dict(lm = 노랗게 칠할 원본 칸 번호, rm = 노랗게 칠할 결과 줄번호, gaps = 원본 내용이 빠진 자리(그 앞 결과 줄번호, 맨 앞 0))"""
    L, Li, R, Ri = [], [], [], []
    for i, b in enumerate(blocks):
        cs = ([c for row in b for cell in row if cell not in ("<<", "^^") for c in content(cell, True)]   # << ^^ = 합친 칸 표시
              if isinstance(b, list) else content(b))
        L += cs
        Li += [i] * len(cs)
    for n, hs in logical(rows):
        if hs[0].lstrip().startswith("<table"):
            cs = [c for line in visible(hs[0]) for c in content(line[4:].replace(" | ", " "), True)]
        else:
            cs = content(" ".join(t for h in hs for t in visible(h)))
        R += cs
        Ri += [n] * len(cs)
    lm, rm, gone, came, gaps = set(), set(), [], [], set()
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, L, R, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if i2 > i1:
            gone.append(("".join(L[i1:i2]), set(Li[i1:i2]), Ri[j1 - 1] if j1 else 0, j2 > j1))
        if j2 > j1:
            came.append(("".join(R[j1:j2]), set(Ri[j1:j2])))
    all_gone, all_came = "".join(g[0] for g in gone), "".join(s for s, _ in came)
    for s, ids, before, replaced in gone:
        if not (len(s) >= 4 and s in all_came):
            lm |= ids
            if not replaced:
                gaps.add(before)
    for s, ids in came:
        if not (len(s) >= 4 and s in all_gone):
            rm |= ids
    return {"lm": lm, "rm": rm, "gaps": gaps}


def gap_text(gaps):
    return ", ".join("맨 앞" if n == 0 else f"{n}번 줄 뒤" for n in sorted(gaps))
