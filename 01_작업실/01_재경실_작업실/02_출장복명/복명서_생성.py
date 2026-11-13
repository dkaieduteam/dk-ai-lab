"""출장 복명 / 외근 복명 xlsx + 기타보고 txt 생성기.

빈 양식(assets/)을 zip 레벨에서 치환한다. openpyxl로 다시 저장하면 인쇄설정·셀 메모·
도형("B. 비용 영수증" 라벨)·vml 이 사라져 결재 양식이 깨지므로 열지 않고 바꿀 곳만 바꾼다.

spec 에 other_report 가 있으면 전자결재 본문에 붙여넣을 기타보고 txt 도 같이 만든다.

사용법:  python 복명서_생성.py spec.json
"""

import io
import json
import os
import re
import sys
import zipfile

from PIL import Image

# 양식 xlsx 는 이 스크립트와 같은 폴더에 둔다
ASSETS = os.path.dirname(os.path.abspath(__file__))

# 영수증 배치용 EMU 상수 (원본 작성본에서 역산한 값)
COLW = 819150         # 열 하나의 폭
ROWH = 319405         # 행 하나의 높이 (25.15pt)
GAP = 300000          # 가로 배치 시 영수증 사이 간격

RPR_TITLE = ('<rPr><b/><u/><sz val="11"/><color theme="1"/><rFont val="본고딕 Medium"/>'
             '<family val="2"/><charset val="129"/></rPr>')
RPR_BODY = ('<rPr><sz val="10"/><color theme="1"/><rFont val="본고딕 Medium"/>'
            '<family val="2"/><charset val="128"/></rPr>')

# 모드별 설정. 영수증 배치(col0/row0/height/방향)는 각 양식의 원본 작성본을 따른다 —
# 1박 이상은 J열부터 가로로 나란히, 당일은 G열에서 아래로 쌓는다.
MODES = {
    "1박이상": {
        "template": "양식_출장복명_1박이상.xlsx",
        "si": {"period": 21, "lodging": 22, "transport": 23},
        "layout": {"col0": 9, "row0": 10, "height": 6252882, "dir": "가로"},
    },
    "당일": {
        "template": "양식_외근복명_당일.xlsx",
        "si": {"period": 34, "transport": 35},
        "layout": {"col0": 6, "row0": 7, "height": 7092763, "dir": "세로"},
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def si(rpr, text):
    return (f'<si><r>{rpr}<t xml:space="preserve">{esc(text)}</t></r>'
            f'<phoneticPr fontId="2" type="noConversion"/></si>')


def load_image(path):
    """영수증 이미지를 JPEG 바이트로. PNG·HEIC 캡처도 그대로 받는다."""
    if path.lower().endswith((".jpg", ".jpeg")):
        data = open(path, "rb").read()
        return data, Image.open(io.BytesIO(data)).size
    im = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88, optimize=True)
    return buf.getvalue(), im.size


def make_anchors(images, layout):
    """영수증을 겹치지 않게 나열한다.

    양식의 기존 슬롯 크기에 억지로 맞추면 휴대폰 캡처가 가로로 늘어나므로,
    높이만 고정하고 폭은 원본 종횡비로 계산한 뒤 누적 좌표로 배치한다.
    """
    cy = layout["height"]
    media, anchors = [], []
    x, row = 0, layout["row0"]
    for i, path in enumerate(images, start=1):
        data, (w, h) = load_image(path)
        media.append(("image1.jpg" if i == 1 else f"image{i}.jpeg", data))
        cx = round(cy * w / h)
        if layout["dir"] == "가로":
            col, off = layout["col0"] + x // COLW, x % COLW
            x += cx + GAP
        else:
            col, off = layout["col0"], 0
        anchors.append(
            f'<xdr:oneCellAnchor><xdr:from><xdr:col>{col}</xdr:col><xdr:colOff>{off}</xdr:colOff>'
            f'<xdr:row>{row}</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>'
            f'<xdr:ext cx="{cx}" cy="{cy}"/>'
            f'<xdr:pic><xdr:nvPicPr><xdr:cNvPr id="{9 + i}" name="그림 {9 + i}"/>'
            f'<xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr></xdr:nvPicPr>'
            f'<xdr:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
            f' r:embed="rId{i}"/><a:stretch><a:fillRect/></a:stretch></xdr:blipFill>'
            f'<xdr:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr></xdr:pic>'
            f'<xdr:clientData/></xdr:oneCellAnchor>')
        if layout["dir"] == "세로":
            row += -(-cy // ROWH) + 1   # 이미지가 차지하는 행 수 + 여유 1행
    return media, anchors


def cell_subs_1bak(spec):
    trans = spec["transport"]["amount"]
    hipass = spec.get("hipass", 0)
    lodge = spec.get("lodging", {}).get("amount", 0)
    meals, misc, wmeals = spec["meals"], spec["misc"], spec.get("weekend_meals", 0)
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


SEPARATOR = "-" * 43


def write_other_report(spec):
    """전자결재 본문에 붙여넣을 기타보고 txt.

    구조 = 교육 일정 블록 / 구분선 / 출장 제목·목적·비용 세부사항.
    메모장·전자결재 편집기에서 줄바꿈이 유지되도록 CRLF·UTF-8(BOM 없음)로 쓴다.
    """
    r = spec.get("other_report")
    if not r:
        return None

    lines = []
    for blk in r.get("schedule", []):
        lines.append(f"[{blk['label']}]")
        lines += [f"- {s}" for s in blk["sessions"]]
        lines.append("")
    if lines:
        lines += [SEPARATOR, ""]
    lines.append(f"출장 제목 : {r['title']}")
    lines.append(f"출장 목적 : {r['purpose']}")
    lines.append("출장비 세부사항 : ")
    lines += [f"- {c}" for c in r.get("cost", [])]

    # xlsx 이름(…_{출장 시작일}.xlsx)을 따라간다 → 출장마다 따로 남는다
    path = os.path.splitext(os.path.abspath(spec["out"]))[0] + "_기타보고.txt"
    with open(path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def build(spec):
    mode = spec["mode"]
    cfg = MODES[mode]
    src = os.path.join(ASSETS, cfg["template"])
    dst = spec["out"]

    media, anchors = make_anchors(spec.get("images", []), cfg["layout"])
    subs, total = (cell_subs_1bak if mode == "1박이상" else cell_subs_dangil)(spec)

    new_si = {cfg["si"]["period"]: si(RPR_TITLE, spec["period"]),
              cfg["si"]["transport"]: si(RPR_BODY, spec["transport"]["text"])}
    if mode == "1박이상" and spec.get("lodging", {}).get("text"):
        new_si[cfg["si"]["lodging"]] = si(RPR_BODY, spec["lodging"]["text"])

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    zin = zipfile.ZipFile(src)
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
