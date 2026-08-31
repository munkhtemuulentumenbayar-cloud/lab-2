"""
Match the 'example' cinematic grade (render_cable_hi1/hi2.png) and apply it
to the target renders (GENDO_INT_D824, render 3).

The example is a cold, desaturated photographic grade: lifted teal-blue
blacks, compressed highlights, mild blue cast.  We reproduce it with
enhance.render_grade and report how close each candidate's tone/colour
signature lands relative to the example.
"""
import os
import sys
import numpy as np
import cv2

from glacial import VOID_DARK
from enhance import render_grade

VOID = (VOID_DARK * 255.0)  # RGB


def load_rgb_alpha(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise IOError(path)
    if im.ndim == 2:
        return cv2.cvtColor(im, cv2.COLOR_GRAY2RGB), None
    if im.shape[2] == 4:
        return cv2.cvtColor(im, cv2.COLOR_BGRA2RGB), im[..., 3].copy()
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB), None


def key_background_alpha(rgb, tol=22, blur=0.8):
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for sy, sx in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]:
        mm = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(gray, mm, (sx, sy), 0, loDiff=tol, upDiff=tol,
                      flags=8 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE)
        mask = cv2.bitwise_or(mask, mm)
    fg = 255 - (mask[1:-1, 1:-1] > 0).astype(np.uint8) * 255
    return cv2.GaussianBlur(fg, (0, 0), blur).astype(np.uint8)


def composite_on_void(rgb, alpha):
    if alpha is None:
        return rgb
    a = (alpha.astype(np.float32) / 255.0)[..., None]
    f = rgb.astype(np.float32)
    return np.clip(f * a + VOID[None, None, :] * (1 - a), 0, 255).astype(np.uint8)


def prep(rgb, alpha):
    """Composite onto void (key white surround if no alpha)."""
    if alpha is None:
        alpha = key_background_alpha(rgb)
    return composite_on_void(rgb, alpha)


def signature(im):
    """Style signature of a BGR uint8 image."""
    b, g, r = im[..., 0].astype(np.float32), im[..., 1].astype(np.float32), im[..., 2].astype(np.float32)
    gray = 0.114 * b + 0.587 * g + 0.299 * r
    p = np.percentile(gray, [5, 25, 50, 75, 95])
    sh = gray < 40
    mid = (gray >= 80) & (gray < 120)
    hi = (gray >= 120) & (gray < 160)
    sig = dict(p5=p[0], p25=p[1], p50=p[2], p75=p[3], p95=p[4], mean=float(gray.mean()))
    for band, name in [(sh, "sh"), (mid, "mid"), (hi, "hi")]:
        if band.sum() < 100:
            sig[name] = None
            continue
        sig[name] = dict(
            br=float(b[band].mean() / max(r[band].mean(), 1e-3)),
            gr=float(g[band].mean() / max(r[band].mean(), 1e-3)),
            lum=float(gray[band].mean()),
            frac=float(band.mean()),
        )
    mx = im.max(axis=2).astype(float)
    mn = im.min(axis=2).astype(float)
    sig["sat"] = float(((mx - mn) / (mx + 1e-4)).mean())
    return sig


def report(tag, sig):
    print(f"{tag:14s} p50={sig['p50']:5.0f} mean={sig['mean']:5.0f} "
          f"p5={sig['p5']:4.0f} p95={sig['p95']:4.0f} sat={sig['sat']:.2f}")
    for band in ("sh", "mid", "hi"):
        s = sig[band]
        if s is None:
            print(f"    {band}: (none)")
        else:
            print(f"    {band}: B/R={s['br']:.2f} G/R={s['gr']:.2f} "
                  f"lum={s['lum']:4.0f} frac={s['frac']:.2f}")


def main():
    example = sys.argv[1]
    targets = sys.argv[2:]
    ref = signature(cv2.imread(example))
    print("=== TARGET (example) ===")
    report(example, ref)

    candidates = [
        dict(darken=0.72, desat=0.75, cool=1.15, fog=0.10,
             shadow_tint=[0.060, 0.095, 0.125]),
        dict(darken=0.70, desat=0.72, cool=1.25, fog=0.10,
             shadow_tint=[0.065, 0.100, 0.130]),
        dict(darken=0.68, desat=0.78, cool=1.10, fog=0.12,
             shadow_tint=[0.070, 0.105, 0.135]),
    ]

    for ci, params in enumerate(candidates):
        print(f"\n=== CANDIDATE {ci} {params} ===")
        for t in targets:
            rgb, alpha = load_rgb_alpha(t)
            comp = prep(rgb, alpha)
            out = render_grade(comp, params)
            sig = signature(cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
            report(f"  {os.path.basename(t)}", sig)


if __name__ == "__main__":
    main()
