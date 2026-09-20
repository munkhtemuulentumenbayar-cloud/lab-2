"""
Grade a render into the Arctic Lens 'Cyber-Glacial' style.

Usage:
    python grade_render.py <input.png> [--modes render,glacial,proto,wireframe]
                                     [--out-dir out] [--keep-alpha]

Handles RGB, RGBA and grayscale inputs. Transparent regions are composited
onto the void colour (VOID_DARK) before grading so the render floats in the
abyssal-blue backdrop; the original alpha is optionally re-attached to the
outputs so they can be re-composited onto deliverable sheets.

Outputs (per mode):
    <name>.<mode>.png   - graded image, flattened on void (or RGBA if --keep-alpha)
    <name>.contact.png  - side-by-side contact sheet (original | each mode)
"""
import os
import sys
import argparse
import numpy as np
import cv2

from glacial import glacial_grade, VOID_DARK
from enhance import render_grade, proto_grade, wireframe_grade, cable_glow_sel

VOID = (VOID_DARK * 255.0)          # RGB float

GRADERS = {
    "render":    render_grade,
    "glacial":   glacial_grade,
    "proto":     proto_grade,
    "wireframe": wireframe_grade,
}


def load(path):
    """Return (rgb_uint8, alpha_uint8). RGB order. Alpha None if no channel."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise IOError(f"cannot read {path}")
    if img.ndim == 2:                       # grayscale
        rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        return rgb, None
    if img.shape[2] == 4:                   # BGRA
        bgra = img
        alpha = bgra[..., 3].copy()
        rgb = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGB)
        return rgb, alpha
    # BGR
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB), None


def composite_on_void(rgb, alpha):
    """Composite RGB over VOID using alpha. Returns uint8 RGB."""
    if alpha is None:
        return rgb
    a = (alpha.astype(np.float32) / 255.0)[..., None]
    f = rgb.astype(np.float32)
    out = f * a + VOID[None, None, :] * (1.0 - a)
    return np.clip(out, 0, 255).astype(np.uint8)


def save_rgb(path, rgb, alpha=None):
    """Save RGB uint8 (optionally with alpha) as PNG."""
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    if alpha is not None:
        bgra = np.dstack([bgr, alpha])
        cv2.imwrite(path, bgra)
    else:
        cv2.imwrite(path, bgr)


def label(img, text, scale=2.0):
    h, w = img.shape[:2]
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, int(scale * 2))
    x = (w - tw) // 2
    y = th + 20
    cv2.rectangle(img, (x - 12, y - th - 12), (x + tw + 12, y + 12), (8, 12, 22), -1)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (125, 235, 255), int(scale * 2), cv2.LINE_AA)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--modes", default="render,glacial,proto", help="comma list of grades")
    ap.add_argument("--out-dir", default="renders")
    ap.add_argument("--keep-alpha", action="store_true")
    args = ap.parse_args()

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    rgb, alpha = load(args.input)
    base = os.path.splitext(os.path.basename(args.input))[0]
    os.makedirs(args.out_dir, exist_ok=True)

    comp = composite_on_void(rgb, alpha)     # render floating on void

    panels = [("original", rgb)]
    for mode in modes:
        grad = GRADERS[mode](comp)
        out_alpha = alpha if args.keep_alpha else None
        out_path = os.path.join(args.out_dir, f"{base}.{mode}.png")
        save_rgb(out_path, grad, out_alpha)
        panels.append((mode, grad))
        print(f"wrote {out_path}")

    # contact sheet
    N = len(panels)
    h = min(p.shape[0] for _, p in panels)
    w = min(p.shape[1] for _, p in panels)
    tiles = []
    for _, p in panels:
        if p.shape[:2] != (h, w):
            p = cv2.resize(p, (w, h), interpolation=cv2.INTER_AREA)
        tiles.append(label(p.copy(), _))
    sheet = np.hstack(tiles)
    sheet_path = os.path.join(args.out_dir, f"{base}.contact.png")
    cv2.imwrite(sheet_path, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
    print(f"wrote {sheet_path}")


if __name__ == "__main__":
    main()
