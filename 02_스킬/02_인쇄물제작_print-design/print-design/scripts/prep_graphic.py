"""이미지 모델이 만든 그래픽(PNG)을 인쇄할 수 있는 상태로 만든다.

    python prep_graphic.py deco.png --width-mm 1300 --dpi 100
    python prep_graphic.py deco.png --width-mm 60 --dpi 300 --mode raster

하는 일
 1. 배경 지우기 — 그림 바깥이 투명하지 않으면(흰 바탕 등) 가장자리와 이어진 바탕색을 지운다.
 2. 여백 자르기 — 투명한 바깥 여백을 잘라 실제 그림 크기로 맞춘다.
 3. 종류 판정 — 색이 몇 개뿐인 플랫 그래픽(실루엣·아이콘·단색 도형)인지, 그라데이션·질감·빛 번짐이 있는지 본다.
 4-a. 플랫 → 벡터로 바꾼다(<이름>_vector.json). 크기와 상관없이 선명하고 색이 CMYK로 정확하다.
 4-b. 그 밖 → 인쇄 위치 크기(--width-mm)와 목표 해상도(--dpi)에 필요한 픽셀까지 고품질로 키운다(<이름>_print.png).

--dpi 를 생략하면 그래픽이 들어갈 인쇄물의 긴 변(--item-mm)으로 정한다(실제 크기 기준): 600mm 이하 300 · 2000mm 미만 150 · 현수막급 50.
현수막은 50% 축소 파일로 만들어도 해상도는 실제 크기 기준으로 본다(축소 파일 안에서는 2배).
결과 파일과 spec.json에 넣을 요소 예시를 출력한다.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

MAX_UPSCALE = 4.0  # 이보다 많이 키워야 하면 경고(그림이 뭉개진다)
UP = 4  # 벡터로 바꿀 때 윤곽을 따는 배율


def auto_dpi(long_side_mm):
    """실제 크기 기준. 작은 인쇄물 300 · 포스터급 150 · 현수막급(2000mm 이상) 50 — build_print.py와 같다."""
    if long_side_mm <= 600:
        return 300
    if long_side_mm < 2000:
        return 150
    return 50


# ── 1. 배경 지우기 ─────────────────────────────────────────────

def ensure_transparent(im):
    """이미 투명하면 그대로. 바탕이 칠해져 있으면 가장자리와 이어진 바탕색만 지운다."""
    from skimage.measure import label

    a = np.asarray(im.convert("RGBA")).copy()
    alpha = a[..., 3]
    edge_alpha = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
    if (edge_alpha < 20).mean() > 0.6:
        return Image.fromarray(a, "RGBA"), "이미 투명"
    rgb = a[..., :3].astype(int)
    edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(edge, axis=0)
    if (np.abs(edge - bg).sum(1) < 40).mean() < 0.85:
        return None, "가장자리 색이 고르지 않아 바탕을 자동으로 지울 수 없음"
    dist = np.abs(rgb - bg).sum(2)
    lab = label(dist < 45, connectivity=1)
    touching = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg_mask = np.isin(lab, list(touching))
    # 경계는 바탕색과의 거리만큼 부드럽게 (흰 테두리가 남지 않게)
    soft = np.clip((dist - 15) / 60, 0, 1)
    new_alpha = np.where(bg_mask, (soft * 255).astype(np.uint8), alpha)
    a[..., 3] = np.minimum(alpha, new_alpha)
    return Image.fromarray(a, "RGBA"), f"바탕색 RGB{tuple(int(v) for v in bg)} 지움"


def trim(im):
    box = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(box) if box else im


# ── 2. 종류 판정 ─────────────────────────────────────────────

def palette_fit(im, max_colors=6):
    """불투명한 부분을 k색으로 줄였을 때 얼마나 맞는지. (k, 팔레트, 픽셀별 번호, 맞는 비율)"""
    a = np.asarray(im)
    solid = a[..., 3] > 200
    soft = (a[..., 3] > 20) & ~solid
    # 색 경계의 안티에일리어싱 픽셀은 빼고, 주변 5x5가 고른 곳만 본다
    rgb_im = Image.fromarray(a[..., :3])
    rng = np.zeros(solid.shape, int)
    for ch in rgb_im.split():
        hi = np.asarray(ch.filter(ImageFilter.MaxFilter(5)), int)
        lo = np.asarray(ch.filter(ImageFilter.MinFilter(5)), int)
        rng = np.maximum(rng, hi - lo)
    a_min = np.asarray(im.getchannel("A").filter(ImageFilter.MinFilter(5)))
    calm = solid & (rng < 30) & (a_min > 200)
    calm_ratio = calm.sum() / max(1, solid.sum())
    px = a[..., :3][calm]
    if len(px) == 0:
        return None
    sample = Image.fromarray(px.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    best = None
    for k in range(2, max_colors + 1):
        q = sample.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
        pal = np.array(q.getpalette()[: 3 * k]).reshape(-1, 3)
        idx = np.asarray(q).reshape(-1)
        err = np.abs(px.astype(int) - pal[idx]).sum(1)
        fit = (err < 36).mean()
        best = (k, pal, fit)
        if fit >= 0.93:
            break
    soft_ratio = soft.sum() / max(1, solid.sum())
    # 질감·하프톤처럼 고른 면이 적으면 플랫이 아니다
    fit = best[2] if calm_ratio >= 0.6 else 0.0
    return best[0], best[1], fit, soft_ratio


# ── 3-a. 벡터로 ───────────────────────────────────────────────

def vectorize(im, pal):
    """팔레트 색마다 영역 윤곽을 따서 다각형으로. 좌표는 그림 크기 기준 0~1."""
    from skimage.filters import gaussian
    from skimage.measure import approximate_polygon, find_contours

    a = np.asarray(im)
    h, w = a.shape[:2]
    rgb = a[..., :3].astype(int)
    inside = a[..., 3] > 127
    d = np.stack([np.abs(rgb - c).sum(2) for c in pal], -1)
    lab = np.where(inside, d.argmin(-1), -1)
    layers = []
    for i, c in enumerate(pal):
        m = lab == i
        area = int(m.sum())
        if area < 20:
            continue
        # 4배로 늘린 뒤 부드럽게 해서 윤곽을 따면 곡선이 각지지 않는다
        big = np.asarray(Image.fromarray((np.pad(m, 2) * 255).astype(np.uint8)).resize(
            ((w + 4) * UP, (h + 4) * UP), Image.Resampling.BILINEAR), float) / 255
        sm = gaussian(big, sigma=UP * 1.1)
        paths = []
        for cont in find_contours(sm, 0.5):
            if len(cont) < 8:
                continue
            poly = approximate_polygon(cont, tolerance=0.35) / UP
            if len(poly) < 3:
                continue
            ys, xs = poly[:, 0] - 2, poly[:, 1] - 2
            if abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1))) / 2 < 6:
                continue  # 아주 작은 부스러기
            paths.append([[round(float(x) / w, 5), round(float(y) / h, 5)] for x, y in zip(xs, ys)])
        if paths:
            layers.append({"rgb": [int(v) for v in c], "area": area, "paths": paths})
    layers.sort(key=lambda l: -l["area"])
    return {"w": w, "h": h, "layers": layers}


# ── 3-b. 키우기 ───────────────────────────────────────────────

def upscale(im, need_w):
    """색과 투명도를 나눠 단계적으로(한 번에 2배 이하) 키우고, 살짝 선명하게."""
    cur = im
    while cur.width < need_w:
        nw = min(need_w, cur.width * 2)
        nh = round(cur.height * nw / cur.width)
        rgb = cur.convert("RGB").resize((nw, nh), Image.Resampling.LANCZOS)
        rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
        al = cur.getchannel("A").resize((nw, nh), Image.Resampling.LANCZOS)
        cur = rgb.convert("RGBA")
        cur.putalpha(al)
    return cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("--width-mm", type=float, required=True, help="인쇄물에 놓일 가로 크기(mm)")
    ap.add_argument("--dpi", type=int, help="목표 해상도. 생략하면 --item-mm로 정한다")
    ap.add_argument("--item-mm", type=float, help="인쇄물 긴 변(mm) — --dpi 자동 결정용")
    ap.add_argument("--mode", choices=["auto", "vector", "raster"], default="auto")
    ap.add_argument("--out", help="결과 파일 이름 앞부분 (기본: 원본 이름)")
    a = ap.parse_args()

    dpi = a.dpi or auto_dpi(a.item_mm or a.width_mm)
    base = a.out or os.path.splitext(a.png)[0]
    im, how = ensure_transparent(Image.open(a.png))
    if im is None:
        sys.exit(f"[다시 만들기] {how}. 이미지 모델에 투명 배경(transparent background) PNG로 다시 만들어 달라고 하세요.")
    im = trim(im)
    print(f"배경: {how} · 그림 크기 {im.width}x{im.height}px")

    mode = a.mode
    fit = palette_fit(im)
    if mode == "auto":
        if fit and fit[2] >= 0.93 and fit[3] < 0.08:
            mode = "vector"
        else:
            mode = "raster"
        if not fit:
            why = "불투명한 부분 없음"
        elif fit[2] == 0:
            why = "고른 색 면이 적음(질감·점 무늬)"
        elif fit[3] >= 0.08:
            why = "반투명한 빛 번짐·그림자가 많음"
        else:
            why = f"{fit[0]}색으로 {fit[2]:.0%} 표현 가능"
        print(f"판정: {'플랫 그래픽 → 벡터' if mode == 'vector' else '그라데이션·질감 있음 → 이미지 키우기'} ({why})")

    h_mm = a.width_mm * im.height / im.width
    if mode == "vector":
        data = vectorize(im, fit[1] if fit else np.array([[0, 0, 0]]))
        out = base + "_vector.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        n = sum(len(l["paths"]) for l in data["layers"])
        print(f"벡터 저장: {out} · {len(data['layers'])}색 · 도형 {n}개 — 크기와 상관없이 선명")
        print(f'spec 요소 예: {{"type": "vector", "path": "{os.path.basename(out)}", "x": 0, "y": 0, "w": {a.width_mm:g}}}')
        return

    need_w = round(a.width_mm / 25.4 * dpi)
    eff = im.width / (a.width_mm / 25.4)
    out = base + "_print.png"
    if im.width >= need_w:
        im.save(out)
        print(f"해상도 충분: {eff:.0f}dpi (목표 {dpi}dpi) → {out}")
    else:
        ratio = need_w / im.width
        im2 = upscale(im, need_w)
        im2.save(out)
        print(f"키움: {im.width}px → {im2.width}px ({ratio:.1f}배) · 실효 {eff:.0f}dpi → {dpi}dpi → {out}")
        if ratio > MAX_UPSCALE:
            print(f"  ※ {ratio:.1f}배는 많이 키운 것입니다. 해상도 수치는 맞지만 세부가 흐릴 수 있습니다. "
                  "그래픽을 더 작게 배치하거나, 이미지 모델에 더 큰 크기로 다시 만들어 달라고 하거나, "
                  "색 수가 적은 플랫 스타일로 바꿔 벡터로 처리하는 방법을 사용자에게 제안하세요.")
    print(f"인쇄 크기 {a.width_mm:g}x{h_mm:.0f}mm")
    print(f'spec 요소 예: {{"type": "image", "path": "{os.path.basename(out)}", "x": 0, "y": 0, "w": {a.width_mm:g}}}')


if __name__ == "__main__":
    main()
