"""눈누(noonnu.cc) 무료 글꼴을 찾고, 인쇄 사용 가능 여부를 확인하고, 인쇄용 TTF·OTF로 받는다.

    python fetch_font.py --tag 명조                       # 태그로 찾기 (제목용·붓글씨·손글씨 바탕 등)
    python fetch_font.py --search 고딕 --pages 2          # 이름·키워드로 찾기
    python fetch_font.py <눈누 링크> --list               # 굵기 목록 + 인쇄 사용 가능 여부
    python fetch_font.py <눈누 링크> --weight 700 --out fonts

글꼴 파일은 눈누 페이지에 올라와 있는 파일을 받아 인쇄용 TTF·OTF로 바꿔 저장한다.
라이선스는 눈누 라이선스 요약표의 「인쇄」 줄로 본다. 「사용 가능」이 아니면 받지 않는다.
"""

import argparse
import html
import io
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://noonnu.cc"
UA = {"User-Agent": "Mozilla/5.0 (print-design skill)"}
FONT_EXT = (".woff2", ".woff", ".ttf", ".otf")
# 눈누 페이지의 font-weight 값은 틀린 경우가 많아 파일 이름의 굵기 표기를 먼저 믿는다 (긴 이름부터 비교)
WEIGHT_WORDS = [
    ("extralight", 200), ("ultralight", 200), ("semibold", 600), ("demibold", 600), ("extrabold", 800),
    ("ultrabold", 800), ("thin", 100), ("hairline", 100), ("light", 300), ("regular", 400), ("book", 400),
    ("medium", 500), ("bold", 700), ("black", 900), ("heavy", 900),
    ("alt", 300), ("brg", 400), ("cbd", 700), ("deb", 800), ("ehv", 900),  # aLt·bRg·cBd 식 표기
]
FAIL = "글꼴 파일(TTF·OTF) 첨부를 요청하세요."


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return html.unescape(r.read().decode("utf-8", "replace"))


def get_bytes(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def weight_from_name(url):
    base = re.sub(r"[^a-z]", "", os.path.splitext(os.path.basename(url))[0].lower())
    for word, w in WEIGHT_WORDS:
        if base.endswith(word):
            return w
    return None


# ── 찾기 ──────────────────────────────────────────────

def find_fonts(search=None, tag=None, pages=1):
    """눈누 목록에서 글꼴 이름·제작사·링크를 모은다."""
    found = {}
    for page in range(1, pages + 1):
        q = {"page": page}
        if search:
            q["search"] = search
        if tag:
            q["tag"] = tag
        text = get(f"{BASE}/index?{urllib.parse.urlencode(q)}")
        cards = re.findall(r'href="/font_page/(\d+)">(.*?)</a>', text, re.S)
        before = len(found)
        for fid, body in cards:
            alt = re.search(r'alt="([^"]+)"', body)
            maker = re.search(r"<p[^>]*>(.*?)</p>", body, re.S)
            if alt and fid not in found:
                found[fid] = (alt.group(1).strip(), strip(maker.group(1)) if maker else "")
        if len(found) == before:
            break  # 새 글꼴이 없으면 끝 (검색어 찾기는 쪽 나눔 없이 상위 결과만 나온다)
    return found


# ── 글꼴 페이지 ───────────────────────────────────────

def parse_page(page_url):
    text = get(page_url)
    title = re.search(r"<title>(.*?)</title>", text, re.S)
    name = title.group(1).split("|")[0].strip() if title else ""
    faces = {}
    for block in re.findall(r"@font-face\s*\{[^}]*\}", text):
        src = re.search(r"url\(\s*['\"]?([^'\")]+)", block)
        if not src or not src.group(1).lower().endswith(FONT_EXT):
            continue
        url = src.group(1)
        if url.startswith("//"):
            url = "https:" + url
        if re.search(r"variable|[-_]vf\b", url, re.I):
            continue  # 가변 글꼴은 굵기가 고정되지 않아 쓰지 않는다
        w = re.search(r"font-weight:\s*(\d+)", block)
        faces[url] = weight_from_name(url) or (int(w.group(1)) if w else 400)
    print_use = None
    i = text.find("라이선스 요약표")
    if i >= 0:
        table = strip(text[i:i + 8000])
        m = re.search(r"인쇄 .*?(사용 가능|조건부 허용|사용 불가|불가)", table)
        if m:
            print_use = m.group(1)
    download = None
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*<span>\s*다운로드 페이지로 이동', text)
    if m:
        download = m.group(1)
    return name, faces, print_use, download


def save_sfnt(data, url, out_dir):
    from fontTools.ttLib import TTFont

    try:
        font = TTFont(io.BytesIO(data))
    except ImportError:
        sys.exit("[받기 실패] WOFF2 파일을 풀려면 brotli가 필요합니다: pip install brotli — 설치가 안 되면 " + FAIL)
    font.flavor = None
    ext = ".otf" if font.sfntVersion == "OTTO" else ".ttf"
    base = os.path.splitext(os.path.basename(url.split("?")[0]))[0]
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, base + ext)
    font.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?", help="눈누 글꼴 페이지 주소 (https://noonnu.cc/font_page/번호)")
    ap.add_argument("--search", help="눈누에서 이름·키워드로 찾기")
    ap.add_argument("--tag", help="눈누 태그로 찾기 (예: 명조, 제목용, 붓글씨, 손글씨 바탕, 장식체)")
    ap.add_argument("--pages", type=int, default=1, help="태그 찾기 결과를 몇 쪽까지 볼지 (한 쪽 약 24개)")
    ap.add_argument("--weight", type=int, default=None, help="굵기 (400=Regular, 500=Medium, 700=Bold). 없으면 400에 가장 가까운 것")
    ap.add_argument("--out", default="fonts")
    ap.add_argument("--list", action="store_true", help="굵기 목록과 인쇄 사용 가능 여부만 보기")
    a = ap.parse_args()

    if a.search or a.tag:
        try:
            found = find_fonts(a.search, a.tag, a.pages)
        except Exception as e:
            sys.exit(f"[찾기 실패] 눈누를 열 수 없습니다 ({e}). 사용자에게 눈누에서 직접 골라 링크를 달라고 요청하세요.")
        if not found:
            sys.exit("[찾기 결과 없음] 다른 키워드·태그로 찾아 보세요.")
        for fid, (name, maker) in found.items():
            print(f"{name} · {maker} · {BASE}/font_page/{fid}")
        print("\n고른 글꼴은 --list로 인쇄 사용 가능 여부를 확인한 뒤 받습니다.")
        return

    if not a.url:
        ap.error("눈누 링크 또는 --search/--tag 가 필요합니다.")
    try:
        name, faces, print_use, download = parse_page(a.url)
    except Exception as e:
        sys.exit(f"[받기 실패] 눈누 페이지를 열 수 없습니다 ({e}). " + FAIL)

    print(f"글꼴: {name}  ({a.url})")
    print(f"인쇄: {print_use or '확인 못 함 — 눈누 페이지 라이선스 요약표를 직접 확인'}")
    for url, w in sorted(faces.items(), key=lambda kv: kv[1]):
        print(f"  굵기 {w}: {os.path.basename(url)}")
    if download:
        print(f"제작사 다운로드 페이지: {download}")
    if print_use and print_use != "사용 가능":
        sys.exit(f"[인쇄 {print_use}] 이 글꼴은 인쇄에 바로 쓸 수 없습니다. "
                 "사용자가 고른 글꼴이면 조건을 원본 라이선스에서 확인해 달라고 알리고, AI가 고르는 중이면 다른 글꼴을 고르세요.")
    if a.list:
        return
    if not faces:
        sys.exit("[받기 실패] 이 페이지에서 굵기가 고정된 글꼴 파일을 찾지 못했습니다. " + FAIL)

    want = a.weight if a.weight is not None else 400
    url = min(faces, key=lambda u: (abs(faces[u] - want), -faces[u]))
    if a.weight is not None and faces[url] != want:
        print(f"  ※ 굵기 {want}가 없어 가장 가까운 {faces[url]}을 씁니다.")
    try:
        path = save_sfnt(get_bytes(url), url, a.out)
    except SystemExit:
        raise
    except Exception as e:
        sys.exit(f"[받기 실패] {os.path.basename(url)}을 받거나 바꾸지 못했습니다 ({e}). " + FAIL)
    print(f"저장: {path}")
    print(f'spec.fonts 예: {{"file": "{path}", "name": "{name}", "noonnu": "{a.url}"}}')


if __name__ == "__main__":
    main()
