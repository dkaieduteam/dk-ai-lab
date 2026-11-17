"""인쇄물 조립기 — 배경(이미지 모델 결과) 위에 글자·도형·로고를 벡터로 얹어
CMYK 인쇄용 PDF를 만든다(종이 인쇄물은 화면 공유용 PNG·JPG도).

색은 CMYK 기준이다. 글자·도형은 CMYK 값으로 그리고, 배경 이미지·로고(RGB)는
CMYK로 변환해 넣는다. 인쇄소가 준 ICC 프로파일이 있으면 그것으로, 없으면 기본 변환식으로.

사용법
    python build_print.py spec.json

spec.json 예시는 SKILL.md 4단계를 본다. 좌표·크기 단위는 mm이고,
기준점은 완성 크기(재단선) 왼쪽 위다. 글자 크기만 pt.
"""
import json
import os
import re
import sys

from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import FILL_EVEN_ODD

MM = 72 / 25.4  # 1mm = 2.8346pt
FONT_KEYS = []  # spec.fonts에 등록한 이름(예: "제목", "본문") 순서
CMAPS = {}  # 이름 → 글꼴에 들어 있는 글자(코드포인트) 집합
FALLBACK = {}  # 이름 → 빠진 글자를 대신 그릴 글꼴 이름
FILE_INFO = {}  # 이름 → (파일 안 글꼴 이름, 굵기 값)
ICC = None  # 인쇄소 ICC 프로파일 경로(spec.icc). 없으면 기본 변환식
HEX_USED = set()  # CMYK로 바꿔 쓴 #RRGGBB 색 — 알림용
OVERLAY = []  # 투명 배경 이미지 — elements 순서대로 층을 쌓을 때 쓴다


# ── CMYK ────────────────────────────────────────────────────────────

def rgb_to_cmyk_array(rgb):
    """RGB(0~1, numpy 배열 ...x3) → CMYK(0~1). 회색·검정은 K(먹)로 보내는 기본 변환식."""
    import numpy as np

    k = 1 - rgb.max(axis=-1)
    d = np.where(k < 1, 1 - k, 1)
    c = (1 - rgb[..., 0] - k) / d
    m = (1 - rgb[..., 1] - k) / d
    y = (1 - rgb[..., 2] - k) / d
    return np.clip(np.stack([c, m, y, k], -1), 0, 1)


def rgb_image_to_cmyk(im):
    """PIL RGB 이미지 → CMYK 이미지."""
    from PIL import Image, ImageCms

    im = im.convert("RGB")
    if ICC:
        return ImageCms.profileToProfile(im, ImageCms.createProfile("sRGB"), ICC,
                                         renderingIntent=0, outputMode="CMYK")
    import numpy as np

    arr = rgb_to_cmyk_array(np.asarray(im, dtype=np.float32) / 255)
    return Image.fromarray((arr * 255).round().astype("uint8"), "CMYK")


def hex_to_cmyk(value):
    from PIL import Image

    h = value.lstrip("#")
    px = Image.new("RGB", (1, 1), tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    return tuple(v / 255 for v in rgb_image_to_cmyk(px).getpixel((0, 0)))


def cmyk_tuple(value):
    """색 지정 → (c, m, y, k) 0~1. 받는 형식: 'cmyk(0,20,60,0)'(%) · [0,20,60,0] · 'K100' · '#RRGGBB'."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return tuple(v / 100 for v in value)
    v = str(value).strip()
    if v.upper() == "K100":
        return (0, 0, 0, 1)
    m = re.fullmatch(r"cmyk\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)", v, re.I)
    if m:
        return tuple(float(x) / 100 for x in m.groups())
    if re.fullmatch(r"#[0-9a-fA-F]{6}", v):
        HEX_USED.add(v.upper())
        return hex_to_cmyk(v)
    sys.exit(f"[중단] 색 형식을 알 수 없습니다: {value} — cmyk(c,m,y,k) 또는 #RRGGBB 또는 K100")


def color(value):
    t = cmyk_tuple(value)
    return CMYKColor(*t) if t else None


def ink_checks(spec, log):
    """잉크 총량 300% 초과(뒷묻음), 작은 글자의 4색 혼합(판 어긋남 번짐)을 알린다."""
    def walk():
        bg = spec.get("background") or {}
        for v in ([bg.get("color")] + list(bg.get("colors", []))):
            yield "배경", v, None
        for i, el in enumerate(spec.get("elements", [])):
            for key in ("color", "fill", "stroke"):
                if el.get(key) is not None:
                    yield f"요소 {i}", el[key], el if el["type"] == "text" else None
    for where, v, text_el in walk():
        if v is None:
            continue
        t = cmyk_tuple(v)
        tac = sum(t) * 100
        if tac > 300:
            log.append(f"{where} 색 {v}: 잉크 총량 {tac:.0f}% — 300%를 넘으면 뒷묻음이 생길 수 있습니다.")
        if text_el and text_el["size"] < 12 and sum(1 for x in t if x > 0.02) >= 2 and t[3] > 0.5:
            log.append(f"{where} 글자 {text_el['size']}pt가 여러 잉크를 섞은 진한 색({v})입니다. "
                       "작은 글자는 판이 어긋나면 번지므로 K100(먹 1도)을 권합니다.")


def prepare_image(path):
    """이미지 → (CMYK JPEG 경로, 투명 마스크 PNG 경로 또는 None, 원본 크기). 결과는 .converted/에 캐시."""
    from PIL import Image

    out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), ".converted")
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0] + ("_icc" if ICC else "")
    jpg, mask = os.path.join(out_dir, stem + "_cmyk.jpg"), os.path.join(out_dir, stem + "_alpha.png")
    with Image.open(path) as im:
        size = im.size
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        if not (os.path.exists(jpg) and os.path.getmtime(jpg) >= os.path.getmtime(path)):
            if im.mode == "CMYK":
                im.save(jpg, quality=95)
            else:
                rgba = im.convert("RGBA")
                rgb_image_to_cmyk(rgba.convert("RGB")).save(jpg, quality=95)
                if has_alpha:
                    rgba.getchannel("A").save(mask)
    return jpg, (mask if has_alpha else None), size



def to_truetype(path):
    """reportlab은 TrueType 윤곽 글꼴만 읽는다. OTF(CFF)면 TTF로 바꾼 사본을 만든다."""
    from fontTools.ttLib import TTFont as FTFont

    font = FTFont(path, lazy=False)
    if "glyf" in font:
        return path
    out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), ".converted")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ".ttf")
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(path):
        return out
    if "CFF2" in font or "fvar" in font:
        sys.exit(f"[중단] 가변 글꼴입니다: {os.path.basename(path)} — 굵기가 고정된 파일(예: -Bold.otf)을 받아 주세요.")
    print(f"  OTF → TTF 변환 중: {os.path.basename(path)} (한글 글꼴은 1분 정도 걸립니다)")
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable

    order = font.getGlyphOrder()
    gset = font.getGlyphSet()
    glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(gset)
        gset[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    font["glyf"] = glyf
    font["loca"] = newTable("loca")
    del font["CFF "]
    if "VORG" in font:
        del font["VORG"]
    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    for k in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
              "maxStackElements", "maxSizeOfInstructions", "maxComponentElements"):
        setattr(maxp, k, 0)
    maxp.maxZones = 1
    font["maxp"] = maxp
    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = order
    font.sfntVersion = "\x00\x01\x00\x00"
    font.save(out)
    return out


def unwrap_woff(path):
    """WOFF·WOFF2 형식 글꼴 파일을 TTF·OTF 사본으로 바꾼다 (눈누에서 받은 파일)."""
    from fontTools.ttLib import TTFont as FTFont

    try:
        font = FTFont(path)
    except ImportError:
        sys.exit("[중단] WOFF2를 풀려면 brotli가 필요합니다: pip install brotli — 설치가 안 되면 TTF·OTF 파일 첨부를 요청하세요.")
    font.flavor = None
    out_dir = os.path.join(os.path.dirname(os.path.abspath(path)), ".converted")
    os.makedirs(out_dir, exist_ok=True)
    ext = ".otf" if font.sfntVersion == "OTTO" else ".ttf"
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + ext)
    font.save(out)
    print(f"  글꼴 파일 형식 변환 → {ext[1:].upper()}: {os.path.basename(path)}")
    return out


def register_fonts(spec):
    """spec.fonts = {"제목": {"file", "name", "noonnu"}, "본문": {...}} — 눈누에서 받은 TTF·OTF."""
    fonts = spec.get("fonts")
    if not fonts:
        sys.exit("[중단] spec.fonts가 없습니다. 눈누에서 받은 글꼴 파일을 지정해 주세요 (SKILL.md 1·4단계).")
    for key, info in fonts.items():
        path = info["file"]
        if not os.path.exists(path):
            sys.exit(f"[중단] 글꼴 파일이 없습니다: {path}")
        if os.path.splitext(path)[1].lower() in (".woff", ".woff2"):
            path = unwrap_woff(path)
        for need in ("name", "noonnu"):
            if not info.get(need):
                sys.exit(f"[중단] fonts.{key}.{need}가 비어 있습니다. 글꼴 이름과 눈누 링크는 저작권 확인용으로 반드시 적습니다.")
        ttf = to_truetype(path)
        pdfmetrics.registerFont(TTFont(f"F-{key}", ttf))
        FONT_KEYS.append(key)
        CMAPS[key], FILE_INFO[key] = read_font_info(ttf)
        if info.get("fallback"):
            FALLBACK[key] = info["fallback"]
    for key, fb in FALLBACK.items():
        if fb not in fonts:
            sys.exit(f"[중단] fonts.{key}.fallback '{fb}'가 spec.fonts에 없습니다.")


def read_font_info(ttf):
    """글꼴에 들어 있는 글자 목록과, 파일 안에 적힌 글꼴 이름·굵기를 읽는다."""
    from fontTools.ttLib import TTFont as FTFont

    f = FTFont(ttf, lazy=True)
    cmap = set(f.getBestCmap() or {})
    names = f["name"]
    ko = names.getName(1, 3, 1, 0x412)  # 한국어 이름이 있으면 우선
    fam = str(ko or names.getDebugName(1) or "?")
    sub = str(names.getName(2, 3, 1, 0x412) or names.getDebugName(2) or "")
    weight = f["OS/2"].usWeightClass if "OS/2" in f else None
    return cmap, (f"{fam} {sub}".strip(), weight)


def pick_font(key, ch):
    """이 글자를 그릴 글꼴 이름. 없으면 대체 글꼴, 그래도 없으면 None."""
    if ch in "\n" or ord(ch) in CMAPS[key]:
        return key
    fb = FALLBACK.get(key)
    if fb and ord(ch) in CMAPS[fb]:
        return fb
    return None


def check_glyphs(spec):
    """모든 문구의 글자가 글꼴에 있는지 먼저 본다. 빠지면 인쇄물에 빈칸·네모로 찍힌다."""
    problems = []
    for i, el in enumerate(spec.get("elements", [])):
        if el["type"] != "text":
            continue
        key = el.get("font", FONT_KEYS[0])
        if key not in FONT_KEYS:
            sys.exit(f"[중단] 요소 {i}의 font '{key}'가 spec.fonts에 없습니다. 있는 이름: {FONT_KEYS}")
        missing = sorted({ch for ch in el["text"] if ch not in " \n" and pick_font(key, ch) is None})
        if missing:
            problems.append(f"  요소 {i} ({key}: {spec['fonts'][key]['name']}) — 없는 글자: {' '.join(missing)}"
                            f"  ← 「{el['text'][:20]}」")
    if problems:
        sys.exit("[중단] 글꼴에 없는 글자가 있습니다. 이대로 인쇄하면 빈칸이나 네모로 찍힙니다.\n"
                 + "\n".join(problems)
                 + "\n해결: ① 해당 글꼴에 fallback(대체 글꼴 이름)을 지정하거나 ② 글꼴을 바꾸거나 ③ 문구를 바꿉니다.")


def segments(key, line):
    """한 줄을 글꼴별 조각으로 나눈다 — 빠진 글자만 대체 글꼴로."""
    segs = []
    for ch in line:
        k = pick_font(key, ch) or key
        if segs and segs[-1][0] == k:
            segs[-1][1] += ch
        else:
            segs.append([k, ch])
    return segs


def line_width(key, line, size, cs):
    return sum(pdfmetrics.stringWidth(t, f"F-{k}", size) for k, t in segments(key, line)) + cs * len(line)


def write_font_credits(spec, out_dir, name):
    """'사용 글꼴' 안내 — 사람이 눈누 링크에서 라이선스를 직접 확인하도록.
    돌려주는 값: (사용자에게 보여 줄 줄들, skill 내부 확인용 파일 대조 줄들)."""
    groups = {}
    for key, info in spec["fonts"].items():
        groups.setdefault((info["name"], info["noonnu"]), []).append(key)
    shown = ["[사용 글꼴] 인쇄 전에 눈누 페이지에서 라이선스를 직접 확인해 주세요."]
    for (fname, link), keys in groups.items():
        shown.append(f"- {'·'.join(keys)}: {fname} · {link}")
    for key, fb in FALLBACK.items():
        shown.append(f"- 「{key}」 글꼴에 없는 글자는 「{fb}」 글꼴로 찍었습니다.")
    internal = []
    for key, info in spec["fonts"].items():
        fam, weight = FILE_INFO.get(key, ("?", None))
        internal.append(f"  {key}: 사용자가 말한 이름 「{info['name']}」 / 파일 {os.path.basename(info['file'])}"
                        f" / 파일 안 이름 「{fam}」" + (f" / 굵기 {weight}" if weight else ""))
    with open(os.path.join(out_dir, f"{name}_사용글꼴.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(shown) + "\n")
    return shown, internal


def print_report(log, credits):
    shown, internal = credits
    print("\n".join(log))
    print()
    print("\n".join(shown))
    print("\n[skill 내부 확인용 — 사용자에게 보여 주지 않는다] 첨부 파일이 말한 글꼴과 같은지 대조:")
    print("\n".join(internal))
    print("  → 이름이 분명히 다른 글꼴이면(같은 글꼴의 영문·한글 표기 차이는 제외) 사용자에게 알린다.")


def auto_dpi(long_side_mm):
    """실제 크기 기준 목표 해상도. 작은 인쇄물 300dpi, 포스터급 150dpi, 현수막급 50dpi(멀리서 본다)."""
    if long_side_mm <= 600:
        return 300
    if long_side_mm < 2000:
        return 150
    return 50


BANNER_MM = 2000  # 긴 변이 이 이상이면 현수막급: 기본 50% 축소 파일로 만든다


def wrap(text, key, size, width_pt, cs=0):
    """줄바꿈(\n)을 지키고, 폭을 넘으면 띄어쓰기 → 글자 단위로 자른다."""
    lines = []
    for para in text.split("\n"):
        if width_pt is None:
            lines.append(para)
            continue
        cur = ""
        for word in para.split(" "):
            trial = (cur + " " + word) if cur else word
            if line_width(key, trial, size, cs) <= width_pt:
                cur = trial
                continue
            if cur:
                lines.append(cur)
            cur = ""
            for ch in word:  # 한 단어가 폭보다 길면 글자 단위로
                if line_width(key, cur + ch, size, cs) > width_pt and cur:
                    lines.append(cur)
                    cur = ch
                else:
                    cur += ch
        lines.append(cur)
    return lines


def draw_background(c, bg, x0, y0, w, h, log):
    bg = bg or {}
    kind = bg.get("type", "color")
    if kind == "color":
        c.setFillColor(color(bg.get("color", "cmyk(0,0,0,0)")))
        c.rect(x0, y0, w, h, stroke=0, fill=1)
    elif kind == "gradient":
        cols = [color(v) for v in bg["colors"]]
        if bg.get("direction", "vertical") == "vertical":
            c.linearGradient(x0, y0 + h, x0, y0, cols, extend=True)
        else:
            c.linearGradient(x0, y0, x0 + w, y0, cols, extend=True)
    elif kind == "image":
        path, _, (iw, ih) = prepare_image(bg["path"])  # CMYK로 바꾼 사본
        # cover: 빈 곳 없이 채우고 넘치는 부분은 잘린다
        scale = max(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        c.saveState()
        p = c.beginPath()
        p.rect(x0, y0, w, h)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(path, x0 + (w - dw) / 2, y0 + (h - dh) / 2, dw, dh)
        c.restoreState()
        eff_dpi = iw / (dw / 72)
        log.append(f"배경 이미지 실효 해상도 약 {eff_dpi:.0f}dpi ({iw}x{ih}px)")
        if eff_dpi < 100:
            log.append("  → 낮음: 확대돼 흐려 보일 수 있습니다. 흐림이 티 나지 않는 그림인지 미리보기로 확인하세요.")


def is_transparent_image(el):
    return el["type"] == "image" and prepare_image(el["path"])[1] is not None


def draw_elements(c, elements, ox, oy_top, safe, trim_w, trim_h, log, target_dpi=300, start=0):
    """ox, oy_top = 재단선 왼쪽 위(pt). 요소 좌표는 mm, 위에서 아래로."""
    for i, el in enumerate(elements, start):
        kind = el["type"]
        x = ox + el.get("x", 0) * MM
        top = oy_top - el.get("y", 0) * MM
        if kind != "line":
            check_safe(el, safe, trim_w, trim_h, i, log)
        if kind == "rect":
            w, h = el["w"] * MM, el["h"] * MM
            fill, stroke = color(el.get("fill")), color(el.get("stroke"))
            if fill:
                c.setFillColor(fill)
            if stroke:
                c.setStrokeColor(stroke)
                c.setLineWidth(el.get("stroke_pt", 1))
            r = el.get("radius", 0) * MM
            c.roundRect(x, top - h, w, h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)
        elif kind == "line":
            c.setStrokeColor(color(el.get("color", "K100")))
            c.setLineWidth(el.get("width_pt", 1))
            c.line(x, top, ox + el["x2"] * MM, oy_top - el["y2"] * MM)
        elif kind == "image":
            jpg, mask, (iw, ih) = prepare_image(el["path"])
            w = el["w"] * MM
            h = el.get("h", el["w"] * ih / iw) * MM
            if mask:  # 투명 배경 이미지는 compose_layers가 순서대로 얹는다
                OVERLAY.append((jpg, mask, x, top, w, h))
            else:
                c.drawImage(jpg, x, top - h, w, h)
            eff = iw / (w / 72)
            if eff < target_dpi * 0.8:
                log.append(f"요소 {i} 이미지({os.path.basename(el['path'])}) 실효 {eff:.0f}dpi — "
                           f"목표 {target_dpi}dpi보다 낮습니다. 그래픽이면 prep_graphic.py --width-mm {el['w']:g} "
                           f"--dpi {target_dpi}로 처리해 다시 넣으세요(로고는 더 큰 원본을 받습니다).")
        elif kind == "vector":
            draw_vector(c, el, x, top)
        elif kind == "text":
            key = el.get("font", FONT_KEYS[0])
            size = el["size"]
            if size < 7:
                log.append(f"요소 {i} 글자 {size}pt: 7pt 미만은 인쇄 시 흐릴 수 있습니다.")
            width = el["w"] * MM if "w" in el else None
            lead = size * el.get("leading", 1.3)
            cs = el.get("letter_spacing", 0)  # pt
            c.setFillColor(color(el.get("color", "K100")))
            baseline = top - size * 0.86
            align = el.get("align", "left")
            for line in wrap(el["text"], key, size, width, cs):
                lw = line_width(key, line, size, cs)
                if align == "center" and width:
                    cx = x + (width - lw) / 2
                elif align == "right" and width:
                    cx = x + width - lw
                else:
                    cx = x
                for k, t in segments(key, line):  # 빠진 글자만 대체 글꼴로 이어 그린다
                    tobj = c.beginText(cx, baseline)
                    tobj.setFont(f"F-{k}", size)
                    tobj.setCharSpace(cs)
                    tobj.textOut(t)
                    c.drawText(tobj)
                    cx += pdfmetrics.stringWidth(t, f"F-{k}", size) + cs * len(t)
                baseline -= lead
        else:
            log.append(f"요소 {i}: 알 수 없는 type '{kind}' — 건너뜀")


def rgb_to_cmyk_color(rgb):
    from PIL import Image

    px = Image.new("RGB", (1, 1), tuple(rgb))
    return CMYKColor(*[v / 255 for v in rgb_image_to_cmyk(px).getpixel((0, 0))])


def draw_vector(c, el, x, top):
    """prep_graphic.py가 만든 벡터 그래픽(<이름>_vector.json)을 CMYK 도형으로 그린다."""
    with open(el["path"], encoding="utf-8") as f:
        data = json.load(f)
    w = el["w"] * MM
    h = el.get("h", el["w"] * data["h"] / data["w"]) * MM
    seam = 0.6 * w / data["w"]  # 색 경계 틈 메우기: 원본 0.6픽셀 굵기의 같은 색 테두리
    for layer in data["layers"]:
        col = rgb_to_cmyk_color(layer["rgb"])
        p = c.beginPath()
        for poly in layer["paths"]:
            p.moveTo(x + poly[0][0] * w, top - poly[0][1] * h)
            for px, py in poly[1:]:
                p.lineTo(x + px * w, top - py * h)
            p.close()
        c.setFillColor(col)
        c.setStrokeColor(col)
        c.setLineWidth(seam)
        c.setLineJoin(1)
        c.drawPath(p, stroke=1, fill=1, fillMode=FILL_EVEN_ODD)


def check_safe(el, safe, trim_w, trim_h, i, log):
    if el["type"] == "rect" and el.get("allow_bleed"):
        return  # 띠 장식처럼 재단선 밖까지 나가도 되는 도형
    x, y = el.get("x", 0), el.get("y", 0)
    w = el.get("w", 0)
    if x < safe or y < safe or x + w > trim_w - safe or y > trim_h - safe:
        log.append(f"요소 {i}({el['type']})가 안전선({safe}mm) 밖에 있습니다. 재단 때 잘릴 수 있습니다.")


def draw_crop_marks(c, ox, oy, w, h, bleed):
    c.setStrokeColor(CMYKColor(1, 1, 1, 1))  # 등록색: 모든 판에 찍히는 재단선
    c.setLineWidth(0.25)
    off, ln = bleed + 1 * MM, 5 * MM
    for cx, cy, dx, dy in [(ox, oy, -1, -1), (ox + w, oy, 1, -1), (ox, oy + h, -1, 1), (ox + w, oy + h, 1, 1)]:
        c.line(cx + dx * off, cy, cx + dx * (off + ln), cy)
        c.line(cx, cy + dy * off, cx, cy + dy * (off + ln))


def compose_layers(pdf, layers, sc=1.0):
    """배경 PDF 위에 층을 elements 순서대로 쌓는다.
    layers: ("pdf", 벡터 층 PDF 경로) 또는 ("img", (jpg, mask, x, top, w, h)) — 투명 배경 이미지는 CMYK + 투명 마스크."""
    if not layers:
        return
    import pymupdf

    doc = pymupdf.open(pdf)
    page = doc[0]
    ph = page.rect.height
    for kind, item in layers:
        if kind == "pdf":
            src = pymupdf.open(item)
            page.show_pdf_page(page.rect, src, 0)  # 글자·도형은 벡터 그대로 얹힌다
            src.close()
            os.remove(item)
            continue
        jpg, mask, x, top, w, h = item
        with open(jpg, "rb") as f1, open(mask, "rb") as f2:
            xref = page.insert_image(pymupdf.Rect(x * sc, ph - top * sc, (x + w) * sc, ph - (top - h) * sc),
                                     stream=f1.read(), mask=f2.read(), overlay=True)
        # PyMuPDF가 붙이는 ICC 색공간을 인쇄소가 읽기 쉬운 기본 색공간으로 바로잡는다
        doc.xref_set_key(xref, "ColorSpace", "/DeviceCMYK")
        smask = doc.xref_get_key(xref, "SMask")
        if smask[0] == "xref":
            doc.xref_set_key(int(smask[1].split()[0]), "ColorSpace", "/DeviceGray")
    tmp = pdf + ".tmp"
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    os.replace(tmp, pdf)


def rasterize(pdf, out_base, dpi, log, clip_mm=None, make_jpg=True):
    """PDF 1쪽을 화면용 PNG(·JPG)로. clip_mm = (left, top, right, bottom) 잘라낼 영역(mm)."""
    import pymupdf
    from PIL import Image

    png, jpg = out_base + ".png", out_base + ".jpg"
    doc = pymupdf.open(pdf)
    clip = pymupdf.Rect(*[v * MM for v in clip_mm]) if clip_mm else None
    doc[0].get_pixmap(dpi=dpi, alpha=False, clip=clip).save(png)
    doc.close()
    with Image.open(png) as im:
        im = im.convert("RGB")
        im.save(png, dpi=(dpi, dpi))
        if make_jpg:
            im.save(jpg, quality=95, dpi=(dpi, dpi), subsampling=0)
        size = im.size
    log.append(f"화면용 PNG{'·JPG' if make_jpg else ''} {size[0]}x{size[1]}px @ {dpi}dpi (RGB — 인쇄에는 PDF를 씁니다)")
    return png


def guide_preview(png, out_path, bleed_mm, safe_mm, trim_w, trim_h):
    """확인용: 재단선(빨강)·안전선(파랑)을 그린 축소 미리보기."""
    from PIL import Image, ImageDraw

    with Image.open(png) as im:
        im = im.convert("RGB")
        k = min(1.0, 1600 / max(im.size))
        im = im.resize((int(im.width * k), int(im.height * k)))
        px = im.width / (trim_w + 2 * bleed_mm)
        d = ImageDraw.Draw(im)
        b, s = bleed_mm * px, (bleed_mm + safe_mm) * px
        d.rectangle([b, b, im.width - b, im.height - b], outline=(220, 0, 0), width=2)
        d.rectangle([s, s, im.width - s, im.height - s], outline=(0, 90, 220), width=1)
        im.save(out_path)


def scale_label(sc):
    return "1/10" if abs(sc - 0.1) < 1e-9 else f"{sc * 100:g}%"


def print_banner_notice(sc, trim_w, trim_h):
    """현수막급 결과에는 발주 파일 주의사항을 반드시 함께 알린다 (SKILL.md 6단계)."""
    if sc == 1:
        how = f"실제 크기({trim_w}x{trim_h}mm) 파일입니다."
    else:
        how = (f"{scale_label(sc)} 축소 파일({trim_w * sc:g}x{trim_h * sc:g}mm)입니다. 발주서에 "
               f"「{scale_label(sc)} 축소 파일 — {1 / sc:g}배 확대해 {trim_w}x{trim_h}mm로 출력」이라고 적어 주세요.")
    print(f"""
[현수막 발주 파일 안내] 사용자에게 그대로 전달한다
- 이 PDF는 {how}
- 글자·도형은 벡터라 크게 늘려도 선명합니다. 그래픽 이미지는 실제 크기 기준으로 확인한 해상도입니다.
- 인쇄소마다 받는 파일 크기가 다릅니다. 인쇄소가 원본 크기(실제 크기) 또는 1/10 크기 파일을 요구하면,
  「원본 크기로 다시 만들어 줘」 또는 「1/10 크기로 다시 만들어 줘」라고 요청해 주세요.""")


def main(spec_path):
    spec_path = os.path.abspath(spec_path)
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    os.chdir(os.path.dirname(spec_path))  # spec 안의 이미지 경로는 spec 파일 기준
    global ICC
    if spec.get("icc"):
        from PIL import ImageCms

        ICC = ImageCms.getOpenProfile(spec["icc"])
    register_fonts(spec)
    check_glyphs(spec)
    trim_w, trim_h = spec["trim_mm"]
    bleed = spec.get("bleed_mm", 2)
    safe = spec.get("safe_mm", 5)
    pdf_only = spec.get("pdf_only", False)  # 현수막류: PDF 하나만 넘긴다
    marks = spec.get("crop_marks", False)
    if pdf_only and marks:
        marks = False
        print("  pdf_only(현수막류)라 재단선 표시를 넣지 않습니다.")
    slug = 10 if marks else 0  # 재단선을 찍을 바깥 여유
    name = spec.get("output_name", "인쇄물")
    out_dir = spec.get("output_dir", os.path.dirname(os.path.abspath(spec_path)))
    os.makedirs(out_dir, exist_ok=True)
    log = []

    # 축척: 현수막급(긴 변 2000mm 이상)은 기본 50% 축소 파일. 인쇄소가 원본(1) 또는 1/10(0.1)을 요구하면 spec.scale로.
    banner = max(trim_w, trim_h) >= BANNER_MM
    sc = float(spec.get("scale", 0.5 if banner else 1.0))
    if (max(trim_w, trim_h) + 2 * (bleed + slug)) * sc > 5080:
        sys.exit(f"[중단] PDF 한 쪽 최대 크기(약 5,080mm)를 넘습니다. spec.scale을 더 작게(예: 0.1 = 1/10 축소) 하세요.")

    page_w = (trim_w + 2 * (bleed + slug)) * MM  # 실제 크기 기준 좌표. 축소는 페이지 크기와 변환으로만 한다
    page_h = (trim_h + 2 * (bleed + slug)) * MM
    ox, oy = (bleed + slug) * MM, (bleed + slug) * MM  # 재단선 왼쪽 아래(pt)
    scale_tag = "" if sc == 1 else ("_1-10축소" if abs(sc - 0.1) < 1e-9 else f"_{sc * 100:g}%축소")
    pdf = os.path.join(out_dir, f"{name}_인쇄용{scale_tag}.pdf")

    def new_canvas(path):
        cv = canvas.Canvas(path, pagesize=(page_w * sc, page_h * sc), initialFontName=f"F-{FONT_KEYS[0]}")
        cv.scale(sc, sc)
        return cv

    c = new_canvas(pdf)
    c.setTitle(name)
    # 배경은 재단 여백까지 채운다
    draw_background(c, spec.get("background"), slug * MM, slug * MM,
                    (trim_w + 2 * bleed) * MM, (trim_h + 2 * bleed) * MM, log)
    dpi = spec.get("dpi") or auto_dpi(max(trim_w, trim_h))
    if marks:
        draw_crop_marks(c, ox, oy, trim_w * MM, trim_h * MM, bleed * MM)
    # elements는 적힌 순서대로 아래→위로 쌓는다. 투명 배경 PNG가 끼면 그 앞뒤로 벡터 층을 나눈다.
    elements = spec.get("elements", [])
    has_alpha = [is_transparent_image(el) for el in elements]
    if not any(has_alpha):
        draw_elements(c, elements, ox, oy + trim_h * MM, safe, trim_w, trim_h, log, dpi)
        layers = []
    else:
        layers, run, run_start = [], [], 0

        def flush(run, run_start):
            if not run:
                return
            lp = pdf + f".layer{len(layers)}.pdf"
            lc = new_canvas(lp)
            draw_elements(lc, run, ox, oy + trim_h * MM, safe, trim_w, trim_h, log, dpi, run_start)
            lc.showPage()
            lc.save()
            layers.append(("pdf", lp))

        for i, el in enumerate(elements):
            if has_alpha[i]:
                flush(run, run_start)
                run, run_start = [], i + 1
                OVERLAY.clear()
                draw_elements(None, [el], ox, oy + trim_h * MM, safe, trim_w, trim_h, log, dpi, i)
                layers.append(("img", OVERLAY.pop()))
            else:
                run.append(el)
        flush(run, run_start)
    c.showPage()
    c.save()
    compose_layers(pdf, layers, sc)
    if sc == 1:
        log.insert(0, f"PDF {trim_w}x{trim_h}mm (재단 여백 {bleed}mm 포함 {trim_w + 2 * bleed}x{trim_h + 2 * bleed}mm)")
    else:
        log.insert(0, f"PDF {scale_label(sc)} 축소 파일 {trim_w * sc:g}x{trim_h * sc:g}mm → 실제 출력 {trim_w}x{trim_h}mm "
                      f"({1 / sc:g}배 확대 출력)")
    if ICC:
        from PIL import ImageCms

        log.insert(1, f"색상: CMYK — 이미지 변환 프로파일 {ImageCms.getProfileDescription(ICC).strip()}")
    else:
        log.insert(1, "색상: CMYK — 이미지는 기본 변환식으로 변환(인쇄소 ICC 프로파일이 있으면 spec.icc로 지정)")
    if HEX_USED:
        log.append(f"#RRGGBB 색 {len(HEX_USED)}개를 CMYK로 바꿔 썼습니다: {', '.join(sorted(HEX_USED))} "
                   "— 회사 색처럼 정확해야 하는 색은 CMYK 값으로 지정하세요.")
    ink_checks(spec, log)
    if max(trim_w, trim_h) >= 1000 and bleed > 0:
        log.append(f"현수막·배너 크기인데 재단 여백이 {bleed}mm입니다. 원단·배너류는 보통 0(완성 크기 그대로)입니다 — 인쇄소가 요구한 값인지 확인하세요.")

    if pdf_only:
        # 넘기는 파일은 PDF 하나. 배치 확인용 미리보기만 숨김 폴더에 작게 만든다(전달하지 않음).
        check_dir = os.path.join(out_dir, ".check")
        os.makedirs(check_dir, exist_ok=True)
        small_dpi = max(10, int(1600 / (max(trim_w, trim_h) * sc / 25.4)))
        png = rasterize(pdf, os.path.join(check_dir, name), small_dpi, [], make_jpg=False)  # pdf_only는 재단선 표시 없음
        if png:
            guide_preview(png, os.path.join(check_dir, f"{name}_배치확인.png"), bleed, safe, trim_w, trim_h)
            os.remove(png)
            log.append(f"전달 파일: PDF만 (배치 확인용 미리보기: .check/{name}_배치확인.png — 전달하지 않음)")
        print_report(log, write_font_credits(spec, check_dir, name))  # 글꼴 목록은 메시지로 알린다
        if banner:
            print_banner_notice(sc, trim_w, trim_h)
        print(f"\n출력 폴더: {out_dir}")
        return

    # 화면용 PNG·JPG — 재단선 표시는 빼고, 재단 여백까지 포함한 영역만
    base = os.path.join(out_dir, name)
    clip = (slug, slug, slug + trim_w + 2 * bleed, slug + trim_h + 2 * bleed) if marks else None
    png = rasterize(pdf, base, dpi, log, clip_mm=clip)
    guide_preview(png, os.path.join(out_dir, f"{name}_확인용_재단선.png"), bleed, safe, trim_w, trim_h)

    print_report(log, write_font_credits(spec, out_dir, name))
    print(f"\n출력 폴더: {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("사용법: python build_print.py spec.json")
    main(sys.argv[1])
