"""출장 복명 / 외근 복명 xlsx + 기타보고 txt 생성기.

빈 양식(assets/)을 zip 레벨에서 치환한다. openpyxl로 다시 저장하면 인쇄설정·셀 메모·
도형("B. 비용 영수증" 라벨)·vml 이 사라져 결재 양식이 깨지므로 열지 않고 바꿀 곳만 바꾼다.

전자결재 본문에 붙여넣을 기타보고 txt(칸 제목만)도 같이 만든다.

영수증은 양식의 「B. 비용 영수증」 네모 칸 안에 한 줄에 두 장까지 나란히 붙이고, 세 번째부터는 그 아래 줄에 붙인다.
표준 라이브러리만 쓴다 (실습 폴더의 휴대용 Python 으로 실행). 영수증 이미지는 PNG · JPG.

사용법:  python "09_프로그램 (열지 않아도 됨)\복명서_생성.py" spec.json   (02_출장복명 에서)
"""

import json
import os
import re
import sys
import struct
import zipfile

# 양식 xlsx 는 이 스크립트와 같은 폴더(skill 의 assets)에서 찾고, 없으면 한 단계 위 폴더(작업실의 02_출장복명)에서 찾는다
ASSETS = os.path.dirname(os.path.abspath(__file__))


def template_path(name):
    for d in (ASSETS, os.path.dirname(ASSETS)):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    sys.exit(f"[양식 없음] {name} 을(를) {ASSETS} 와 그 위 폴더에서 찾지 못했습니다")

# 영수증 배치용 EMU 상수 (원본 작성본에서 역산한 값)
COLW = 819150         # 열 하나의 폭 (네모 칸 안 열은 모두 10.75)
PT = 12700            # 1pt
GAP = 150000          # 영수증 사이 · 네모 칸 테두리와의 간격
PER_ROW = 2           # 한 줄에 나란히 붙이는 장수
LODGE_CAP = 70000     # 숙박비 1박 한도 (넘으면 한도까지만 넣는다)

RPR_TITLE = ('<rPr><b/><u/><sz val="11"/><color theme="1"/><rFont val="본고딕 Medium"/>'
             '<family val="2"/><charset val="129"/></rPr>')
RPR_BODY = ('<rPr><sz val="10"/><color theme="1"/><rFont val="본고딕 Medium"/>'
            '<family val="2"/><charset val="128"/></rPr>')

# 모드별 설정. box = 「B. 비용 영수증」 네모 칸 (0부터 센 열 · 행). 1박 이상 = I~V열 11행부터, 당일 = G~L열 8행부터
# max_h = 영수증 한 장의 최대 높이 (원본 작성본의 높이)
MODES = {
    "1박이상": {
        "template": "양식_출장복명_1박이상.xlsx",
        "si": {"period": 21, "lodging": 22, "transport": 23},
        "box": {"col0": 8, "cols": 14, "row0": 10, "max_h": 6252882},
    },
    "당일": {
        "template": "양식_외근복명_당일.xlsx",
        "si": {"period": 34, "transport": 35},
        "box": {"col0": 6, "cols": 6, "row0": 7, "max_h": 7092763},
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def si(rpr, text):
    return (f'<si><r>{rpr}<t xml:space="preserve">{esc(text)}</t></r>'
            f'<phoneticPr fontId="2" type="noConversion"/></si>')


def image_size(data):
    """PNG · JPG 의 (폭, 높이). 다른 형식이면 멈춘다"""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24]), "png"
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            mark, size = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= mark <= 0xCF and mark not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return (w, h), "jpeg"
            i += 2 + size
    raise SystemExit("[영수증 형식] PNG · JPG 만 붙일 수 있습니다. 캡처를 PNG 로 다시 저장해 주세요")


def row_tops(sheet_xml, upto):
    """행 위쪽 좌표(EMU) 목록. 행 높이는 시트의 <row ht> · 없으면 기본 높이"""
    default = float(re.search(r'defaultRowHeight="([\d.]+)"', sheet_xml).group(1))
    hts = {int(r) - 1: float(h) for r, h in re.findall(r'<row r="(\d+)"[^>]*?ht="([\d.]+)"', sheet_xml)}
    tops, y = [], 0
    for r in range(upto):
        tops.append(y)
        y += round(hts.get(r, default) * PT)
    return tops


def make_anchors(images, box, sheet_xml):
    """영수증을 네모 칸 안에 한 줄 두 장씩 붙인다. 폭 · 높이 비율은 원본 그대로"""
    per = 1 if len(images) == 1 else PER_ROW               # 영수증이 한 장이면 칸 폭을 다 쓴다
    slot_w = (box["cols"] * COLW - GAP * (per + 1)) // per
    tops = row_tops(sheet_xml, 400)
    left = box["col0"] * COLW
    y = tops[box["row0"]] + GAP
    media, anchors, line = [], [], []
    for i, path in enumerate(images, start=1):
        data = open(path, "rb").read()
        (w, h), ext = image_size(data)
        k = min(slot_w / w, box["max_h"] / h)
        line.append((i, data, ext, round(w * k), round(h * k)))
        if len(line) == PER_ROW or i == len(images):
            for j, (n, data, ext, cx, cy) in enumerate(line):
                x = left + GAP + j * (slot_w + GAP) + (slot_w - cx) // 2
                row = max(r for r in range(len(tops)) if tops[r] <= y)
                media.append((f"image{n}.{ext}", data))
                anchors.append(
                    f'<xdr:oneCellAnchor><xdr:from><xdr:col>{x // COLW}</xdr:col><xdr:colOff>{x % COLW}</xdr:colOff>'
                    f'<xdr:row>{row}</xdr:row><xdr:rowOff>{y - tops[row]}</xdr:rowOff></xdr:from>'
                    f'<xdr:ext cx="{cx}" cy="{cy}"/>'
                    f'<xdr:pic><xdr:nvPicPr><xdr:cNvPr id="{9 + n}" name="그림 {9 + n}"/>'
                    f'<xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr></xdr:nvPicPr>'
                    f'<xdr:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
                    f' r:embed="rId{n}"/><a:stretch><a:fillRect/></a:stretch></xdr:blipFill>'
                    f'<xdr:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                    f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr></xdr:pic>'
                    f'<xdr:clientData/></xdr:oneCellAnchor>')
            y += max(cy for *_, cy in line) + GAP
            line = []
    return media, anchors


def cell_subs_1bak(spec):
    trans = spec["transport"]["amount"]
    hipass = spec.get("hipass", 0)
    lodge = spec.get("lodging", {}).get("amount", 0)
    meals, misc, wmeals = spec["meals"], spec["misc"], spec.get("weekend_meals", 0)
    cap = LODGE_CAP * max(meals, 1)  # 숙박비 한도 = 1박 70,000원 × 박 수 (박 수 = 식비 횟수)
    if lodge > cap:
        print(f"[숙박 한도] 실결제 {lodge:,}원 → {cap:,}원만 넣음 (1박 {LODGE_CAP:,}원 × {max(meals, 1)}박)")
        lodge = cap
    total = trans + hipass + lodge + 16000 * meals + 8000 * wmeals + 20000 * misc
    subs = [
        ('<c r="C2" s="15"><f>E11+E12</f><v>0</v></c>',
         f'<c r="C2" s="15"><f>E11+E12</f><v>{trans + hipass}</v></c>'),
        ('<c r="C3" s="15"><f>E13</f><v>0</v></c>',
         f'<c r="C3" s="15"><f>E13</f><v>{lodge}</v></c>'),
        ('<c r="C4" s="15"><f>(16000*F14)+(8000*F16)</f><v>0</v></c>',
         f'<c r="C4" s="15"><f>(16000*F14)+(8000*F16)</f><v>{16000 * meals + 8000 * wmeals}</v></c>'),
        ('<c r="C5" s="15"><f>20000*F15</f><v>0</v></c>',
         f'<c r="C5" s="15"><f>20000*F15</f><v>{20000 * misc}</v></c>'),
        ('<c r="C6" s="15"><f>SUM(C2:C5)</f><v>0</v></c>',
         f'<c r="C6" s="15"><f>SUM(C2:C5)</f><v>{total}</v></c>'),
        ('<c r="E11" s="16"><v>0</v></c>', f'<c r="E11" s="16"><v>{trans}</v></c>'),
        ('<c r="E12" s="16"><v>0</v></c>', f'<c r="E12" s="16"><v>{hipass}</v></c>'),
        ('<c r="E13" s="16"><v>0</v></c>', f'<c r="E13" s="16"><v>{lodge}</v></c>'),
        ('<c r="F14" s="11"><v>0</v></c>', f'<c r="F14" s="11"><v>{meals}</v></c>'),
        ('<c r="F15" s="26"><v>0</v></c>', f'<c r="F15" s="26"><v>{misc}</v></c>'),
        ('<c r="F16" s="29"><v>0</v></c>', f'<c r="F16" s="29"><v>{wmeals}</v></c>'),
        # 검증식 캐시 — 식비 횟수는 잡비 횟수보다 적어야 정상
        ('<v>식비 횟수 오류</v>',
         f'<v>식비 횟수 {"오류" if meals >= misc else "정상"}</v>'),
    ]
    if not spec.get("lodging", {}).get("text"):
        subs.append(('<c r="D13" s="28" t="s"><v>22</v></c>', '<c r="D13" s="28"/>'))
    return subs, total


def cell_subs_dangil(spec):
    trans = spec["transport"]["amount"]
    hipass = spec.get("hipass", 0)
    misc = spec.get("misc_amount", 0)
    total = trans + hipass + misc
    subs = [
        ('<c r="C2" s="15"><f>E9+E10</f><v>0</v></c>',
         f'<c r="C2" s="15"><f>E9+E10</f><v>{trans + hipass}</v></c>'),
        ('<c r="C3" s="15"><f>E11</f><v>0</v></c>',
         f'<c r="C3" s="15"><f>E11</f><v>{misc}</v></c>'),
        ('<c r="C4" s="15"><f>C3+C2</f><v>0</v></c>',
         f'<c r="C4" s="15"><f>C3+C2</f><v>{total}</v></c>'),
        ('<c r="E9" s="11"><v>0</v></c>', f'<c r="E9" s="11"><v>{trans}</v></c>'),
        ('<c r="E10" s="11"><v>0</v></c>', f'<c r="E10" s="11"><v>{hipass}</v></c>'),
        ('<c r="E11" s="11"><v>0</v></c>', f'<c r="E11" s="11"><v>{misc}</v></c>'),
    ]
    return subs, total


def write_other_report(spec):
    """전자결재 본문에 붙여넣을 기타보고 txt. 칸 제목만 두고 내용은 사람이 채운다.

    메모장 · 전자결재 편집기에서 줄바꿈이 유지되도록 CRLF · UTF-8(BOM 없음)로 쓴다.
    """
    # xlsx 이름(…_{출장지}_{출장 시작일}.xlsx)을 따라간다 → 출장마다 따로 남는다
    path = os.path.splitext(os.path.abspath(spec["out"]))[0] + "_기타보고.txt"
    with open(path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("출장 목적 : \n내용 : \n")
    return path


def build(spec):
    mode = spec["mode"]
    cfg = MODES[mode]
    src = template_path(cfg["template"])
    dst = spec["out"]

    zin = zipfile.ZipFile(src)
    media, anchors = make_anchors(spec.get("images", []), cfg["box"], zin.read("xl/worksheets/sheet3.xml").decode())
    subs, total = (cell_subs_1bak if mode == "1박이상" else cell_subs_dangil)(spec)

    new_si = {cfg["si"]["period"]: si(RPR_TITLE, spec["period"]),
              cfg["si"]["transport"]: si(RPR_BODY, spec["transport"]["text"])}
    if mode == "1박이상" and spec.get("lodging", {}).get("text"):
        new_si[cfg["si"]["lodging"]] = si(RPR_BODY, spec["lodging"]["text"])

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        n = item.filename
        if n.startswith("xl/media/"):
            continue
        data = zin.read(n)

        if n == "xl/sharedStrings.xml":
            s = data.decode()
            blocks = list(re.finditer(r"<si>.*?</si>", s, re.S))
            out, last = [], 0
            for i, m in enumerate(blocks):
                out.append(s[last:m.start()])
                out.append(new_si.get(i, m.group(0)))
                last = m.end()
            out.append(s[last:])
            data = "".join(out).encode()

        elif n == "xl/worksheets/sheet3.xml":
            s = data.decode()
            for a, b in subs:
                if s.count(a) != 1:
                    raise SystemExit(f"[양식 불일치] {n} 에서 {s.count(a)}건: {a}")
                s = s.replace(a, b)
            data = s.encode()

        elif n == "xl/drawings/drawing3.xml":
            s = data.decode()
            data = s.replace("</xdr:wsDr>", "".join(anchors) + "</xdr:wsDr>").encode()

        elif n == "xl/drawings/_rels/drawing3.xml.rels":
            rels = "".join(
                f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/'
                f'officeDocument/2006/relationships/image" Target="../media/{nm}"/>'
                for i, (nm, _) in enumerate(media, start=1))
            data = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                    f'relationships">{rels}</Relationships>').encode()

        elif n == "[Content_Types].xml":
            s = data.decode()
            for ext, ct in (("png", "image/png"), ("jpeg", "image/jpeg")):
                if f'Extension="{ext}"' not in s:
                    s = s.replace("<Default ", f'<Default Extension="{ext}" ContentType="{ct}"/><Default ', 1)
            data = s.encode()

        elif n == "xl/workbook.xml" and spec.get("sheet_name"):
            data = re.sub(r'(<sheet name=")[^"]+("[^>]*r:id="rId3"/>)',
                          lambda m: m.group(1) + spec["sheet_name"] + m.group(2),
                          data.decode()).encode()

        zout.writestr(item, data)

    for nm, b in media:
        zout.writestr("xl/media/" + nm, b)
    zout.close()
    zin.close()
    return total, len(media), write_other_report(spec)


if __name__ == "__main__":
    spec_path = os.path.abspath(sys.argv[1])
    spec = json.load(open(spec_path, encoding="utf-8"))
    # images · out 상대경로는 spec.json 이 있는 폴더 기준 (어디서 실행해도 같은 결과)
    os.chdir(os.path.dirname(spec_path))
    total, n_img, txt = build(spec)
    print(f"생성: {spec['out']}")
    print(f"합계 {total:,}원 · 영수증 {n_img}장")
    if txt:
        print(f"기타보고: {txt}")
