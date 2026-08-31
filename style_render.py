"""
Arctic Lens — restyle a full render into the 'Cyber-Glacial' signature look.

Pipeline (all from enhance.py / glacial.py):
  1. composite transparent render onto the abyssal void
  2. render_grade   -> cold cinematic photographic base (dark/desat/cool/fog)
  3. cable_glow_sel -> cyan/emerald bioluminescent accents on bright linework
  4. vignette_factor-> nebula edge falloff (repo signature)

Usage:
    python style_render.py <input.png> [--out out/<name>.cyberglacial.png]
"""
import os
import sys
import numpy as np
import cv2

from glacial import VOID_DARK, glacial_grade_alpha
from enhance import render_grade, cable_glow_sel, vignette_factor

VOID = (VOID_DARK * 255.0)
WHITE = np.array([255.0, 255.0, 255.0], np.float32)


def load_rgb_alpha(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise IOError(f"cannot read {path}")
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB), None
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB), img[..., 3].copy()
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB), None


def composite_on_void(rgb, alpha):
    if alpha is None:
        return rgb
    a = (alpha.astype(np.float32) / 255.0)[..., None]
    f = rgb.astype(np.float32)
    return np.clip(f * a + VOID[None, None, :] * (1 - a), 0, 255).astype(np.uint8)


def composite_on_white(rgb, alpha):
    """Composite transparent render onto white so empty pixels read as
    'background' (BG assumption) and become transparent in the grade."""
    if alpha is None:
        return rgb
    a = (alpha.astype(np.float32) / 255.0)[..., None]
    f = rgb.astype(np.float32)
    return np.clip(f * a + WHITE[None, None, :] * (1 - a), 0, 255).astype(np.uint8)


def glacial_transparent(rgb, alpha, params=None):
    """Glacial neon linework with transparent background -> uint8 RGBA."""
    comp = composite_on_white(rgb, alpha)
    return glacial_grade_alpha(comp, params)


PRESETS = {
    "balanced": dict(
        base=dict(darken=0.62, desat=0.70, cool=1.18,
                  fog=0.12, shadow_tint=[0.045, 0.085, 0.120]),
        glow=dict(amt=0.90, weight=0.38, bloom=11),
        vig=0.30),
    "moody": dict(
        base=dict(darken=0.48, desat=0.62, cool=1.38,
                  fog=0.20, shadow_tint=[0.040, 0.075, 0.110]),
        glow=dict(amt=1.00, weight=0.44, bloom=12),
        vig=0.44),
    "luminous": dict(
        base=dict(darken=0.74, desat=0.66, cool=1.10,
                  fog=0.07, shadow_tint=[0.045, 0.085, 0.120]),
        glow=dict(amt=1.20, weight=0.52, bloom=13),
        vig=0.20),
}


def cyberglacial_style(rgb, alpha=None,
                       base=None, glow=None, vig=None,
                       preset=None):
    """Return styled uint8 RGB (optionally with original alpha re-attached)."""
    if preset:
        p = PRESETS[preset]
        base = base or p["base"]
        glow = glow or p["glow"]
        vig = vig if vig is not None else p["vig"]
    base = base or dict(darken=0.62, desat=0.70, cool=1.18,
                        fog=0.12, shadow_tint=[0.045, 0.085, 0.120])
    glow = glow or dict(amt=0.9, weight=0.38, bloom=11)
    vig = 0.30 if vig is None else vig

    comp = composite_on_void(rgb, alpha)
    out = render_grade(comp, base)
    out = cable_glow_sel(out, glow)

    # nebula vignette (multiply)
    h, w = out.shape[:2]
    v = vignette_factor(h, w) * vig
    out = (out.astype(np.float32) * (1 - v[..., None]))
    out = np.clip(out, 0, 255).astype(np.uint8)
    return out


def save(path, rgb, alpha=None):
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, np.dstack([bgr, alpha]) if alpha is not None else bgr)


def save_rgba(path, rgba):
    """Save uint8 RGBA (RGB order) as BGRA PNG with alpha."""
    bgra = np.dstack([rgba[..., 2], rgba[..., 1], rgba[..., 0], rgba[..., 3]])
    cv2.imwrite(path, bgra)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src:
        print("usage: python style_render.py <input.png> [out_path] [--preset balanced|moody|luminous|glacial]")
        sys.exit(1)
    out_path = None
    preset = None
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--preset"):
            if "=" in a:
                preset = a.split("=", 1)[1]
            elif i + 1 < len(args):
                i += 1
                preset = args[i]
            else:
                preset = "balanced"
        elif not a.startswith("--"):
            out_path = a
        i += 1

    rgb, alpha = load_rgb_alpha(src)
    base = os.path.splitext(os.path.basename(src))[0]

    # --- glacial with transparent background --------------------------------
    if preset == "glacial":
        rgba = glacial_transparent(rgb, alpha)
        if out_path is None:
            out_path = os.path.join("renders", f"{base}.glacial-transparent.png")
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        save_rgba(out_path, rgba)
        print(f"wrote {out_path}")
        return

    styled = cyberglacial_style(rgb, alpha, preset=preset)

    if out_path is None:
        tag = f".{preset}" if preset else ".cyberglacial"
        out_path = os.path.join("renders", f"{base}{tag}.png")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # flattened-on-void deliverable + alpha-preserving twin
    save(out_path, styled)
    if alpha is not None:
        ap = out_path.replace(".png", ".alpha.png")
        save(ap, styled, alpha)
        print(f"wrote {ap} (alpha preserved)")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
