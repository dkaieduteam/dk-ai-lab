# -*- coding: utf-8 -*-
"""마스킹 — 품의서 본문의 양식은 그대로 두고 그 밖의 글자는 모두 같은 글자 수로 가린다.

    python 마스킹.py <txt 파일>     가린 결과를 화면에 보여 준다 (시험용)

남기는 것 = 양식만. 줄 앞 공백 · 빈 줄 · 탭 · 「아래」 줄 · 줄 앞 번호(1. 가. 1) 가) (1) (가) ① ㉮ Ⅰ. □ ○ - · , 전각 １． 포함)
           · 줄 안의 가. 나. (가) (나) (1) (2) · 동그라미 번호(① ㉮ ㉠) · 문장부호와 기호(* ( ) : · ※ - 등)
           · 변환 프로그램이 양식으로 보는 말(FORM : 아래 · 다음 · 끝 · 이상 · 붙임 · 첨부 · 별첨 · 제목)
가리는 것 = 그 밖의 모든 글자. 한글 · 한자 → ○, 영문 → A, 숫자 → 0, 전각 숫자 · 영문 → ０ · Ａ (글자 수 · 자리 수는 그대로)
글자 수를 그대로 두므로 가린 샘플로 HTML을 만들면 줄맞춤 · 공백 모양이 원본과 같게 나온다.
양식 말 밖에는 남기지 않으므로 사람이 샘플을 확인하지 않고 AI작업실로 보낸다.
평소에는 「품의서 HTML 만들기」가 이 프로그램을 부른다. Python 표준 라이브러리만 쓴다.
"""
import re
import sys
import unicodedata
from pathlib import Path

AREA = re.compile(r"^\s*-{3,}\s*아\s*래\s*-{3,}\s*$")                       # -----  아  래  -----
KOR = "가나다라마바사아자차카타파하"
NUMBERING = re.compile(r"^((?:[\d０-９]{1,2}[.．)）]|[가나다라마바사아자차카타파하][.．)）]|[(（][\d０-９]{1,2}[)）]|[(（][가나다라마바사아자차카타파하][)）]"
                       r"|[①-⑳㉮-㉻㉠-㉭]|[Ⅰ-Ⅹ]\.?|(?:VIII|VII|VI|IV|IX|III|II|I|V|X)\.(?=\s)"
                       r"|[-–—‐‑－―ㅡ−](?:\s*\.)?|[*·•∙ㆍ‧※□■◆▶◼▪○◇▷●◦]|ㅇ(?=\s))\s*)")
TOKEN = re.compile(r"(?P<ws>\s+)|(?P<word>[가-힣A-Za-z]+)|(?P<num>\d+)|(?P<etc>.)")

# 변환 프로그램이 양식으로 알아보는 말 (「아래」 줄 · 끝 표시 · 붙임 줄 · 제목 줄). 품의 내용이 아니라서 남긴다
FORM = {"아래", "다음", "끝", "이상", "붙임", "첨부", "별첨", "제목"}
CIRCLED = set("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉮㉯㉰㉱㉲㉳㉴㉵㉶㉷㉸㉹㉺㉻㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩㉪㉫㉬㉭ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ")


def cover(s):
    """글자 수를 그대로 두고 가린다 (전각 글자는 전각으로 가려 칸 수도 그대로)"""
    out = []
    for ch in s:
        wide = unicodedata.east_asian_width(ch) in "WF"
        if ch in CIRCLED:
            out.append(ch)                      # 동그라미 번호 · 로마 숫자는 순번(양식)이라 남긴다
        elif re.match(r"[가-힣ㄱ-ㆎ一-鿿]", ch):
            out.append("○")
        elif ch.isdigit() or ch.isnumeric():
            out.append("０" if wide else "0")
        elif ch.isalpha():
            out.append("○" if wide and not "Ａ" <= ch <= "ｚ" else "Ａ" if wide else "A")
        else:
            out.append(ch)
    return "".join(out)


class Masker:
    def text(self, s):
        toks = [(m.lastgroup, m.group()) for m in TOKEN.finditer(s)]
        keep = [kind == "word" and tok in FORM for kind, tok in toks]
        # 글자 사이를 띄어 쓴 양식 말 (아 래 · 제 목) 은 붙여서 본다
        i = 0
        while i < len(toks):
            if toks[i][0] == "word" and len(toks[i][1]) == 1:
                j, idx = i, [i]
                while j + 2 < len(toks) and toks[j + 1][0] == "ws" and toks[j + 2][0] == "word" and len(toks[j + 2][1]) == 1:
                    j += 2
                    idx.append(j)
                if len(idx) > 1:
                    if "".join(toks[k][1] for k in idx) in FORM:
                        for k in idx:
                            keep[k] = True
                    i = j + 1
                    continue
            i += 1
        # 줄 안에 쓴 하위 번호 (… 가. ○○  나. ○○ / … (가) … (나) / … (1) … (2)) 는 남긴다
        for k, (kind, tok) in enumerate(toks):
            if kind == "num" and len(tok) <= 2 and 0 < k < len(toks) - 1 and toks[k - 1][1] in ("(", "（") \
                    and toks[k + 1][1] in (")", "）") and (k == 1 or toks[k - 2][0] == "ws"):
                keep[k] = True
            if kind == "word" and tok in KOR and (k == 0 or toks[k - 1][0] == "ws"):
                if k + 1 < len(toks) and toks[k + 1][1] in (".", "．"):
                    keep[k] = True
            if kind == "word" and tok in KOR and 0 < k < len(toks) - 1 and toks[k - 1][1] in ("(", "（") \
                    and toks[k + 1][1] in (")", "）") and (k == 1 or toks[k - 2][0] == "ws"):
                keep[k] = True
        out = []
        for k, (kind, tok) in enumerate(toks):
            if kind in ("word", "num", "etc") and not keep[k]:
                out.append(cover(tok))          # 숫자 → 0, 한자 → ○, 문장부호는 그대로
            else:
                out.append(tok)
        return "".join(out)

    def line(self, t):
        if not t.strip() or AREA.match(t):
            return t
        lead = t[: len(t) - len(t.lstrip())]
        rest = t[len(lead):]
        m = NUMBERING.match(rest)
        pre = m.group(1) if m else ""
        return lead + pre + self.text(rest[len(pre):])

    def blocks(self, blocks):
        """줄(str) · 표(list of rows) 목록을 가린다"""
        return [[[self.line(c) for c in row] for row in b] if isinstance(b, list) else self.line(b) for b in blocks]


def to_text(blocks):
    """가린 줄 · 표를 txt 로 (표는 | 칸 | 칸 |)"""
    out = []
    for b in blocks:
        if isinstance(b, list):
            out += ["| " + " | ".join(c.replace("|", "/") for c in row) + " |" for row in b]
        else:
            out.append(b)
    return "\n".join(out) + "\n"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    mk = Masker()
    for a in args:
        lines = Path(a).read_text(encoding="utf-8-sig").splitlines()
        print(to_text(mk.blocks(lines)), end="")


if __name__ == "__main__":
    main()
