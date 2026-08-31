"""
Cyber-Glacial / Abyssal Bioluminescence grade for 'The Arctic Lens' boards.
Deterministic, pixel-level color & tone transformation that preserves ALL
geometry, linework, panel divisions and typography exactly in place.
"""
import numpy as np
import cv2

# ---- palette (0..1 floats) -------------------------------------------------
VOID_DARK  = np.array([0.039, 0.059, 0.102])   # #0A0F1A deep space void
VOID_LIGHT = np.array([0.085, 0.140, 0.205])   # subtle glacial blue-gray depth
ICE_CYAN   = np.array([0.490, 0.922, 1.000])   # #7DEBFF primary active system
EMERALD    = np.array([0.224, 1.000, 0.690])   # #39FFB0 secondary ecological
ICE_WHITE  = np.array([0.880, 0.975, 1.000])   # near-white icy highlight

BG = 0.965            # assumed background canvas luminance


def to_float(img):
    return img.astype(np.float32) / 255.0


def from_float(f):
    return np.clip(f * 255.0, 0, 255).astype(np.uint8)


def screen(base, add, k=1.0):
    """Layered screen (lighten) composite limited by k."""
    add = np.clip(add, 0, 1) * k
    return 1.0 - (1.0 - base) * (1.0 - add)


def glacial_grade(img, params=None):
    """Main grade. img: HxWx3 uint8. Returns HxWx3 uint8."""
    p = params or {}
    line_lo      = p.get("line_lo", 0.20)       # darkness considered full line
    blur_sigma   = p.get("blur_sigma", 6.0)     # for boldness separation
    glow_sigma   = p.get("glow_sigma", 12.0)
    glow_amount  = p.get("glow_amount", 0.55)
    cyan_bias    = p.get("cyan_bias", 0.55)     # where bold->cyan crossover sits
    white_core   = p.get("white_core", 0.35)
    void_depth   = p.get("void_depth", 0.55)

    f = to_float(img)
    rgb = f[..., :3]
    gray = (0.2126*rgb[...,0] + 0.7152*rgb[...,1] + 0.0722*rgb[...,2])

    # --- line strength: 0 = background/fill, 1 = full dark stroke -----------
    line = np.clip((BG - gray) / max(BG - line_lo, 1e-3), 0, 1)
    line = line ** p.get("line_gamma", 1.4)

    # --- boldness: thick primary strokes vs thin secondary/contours --------
    blurred = cv2.GaussianBlur(line, (0, 0), blur_sigma)
    ratio = blurred / (line + 1e-4)
    bold = np.clip((ratio - 0.45) / 0.40, 0, 1)          # 0 thin -> 1 thick
    tfactor = np.clip((bold - (1-cyan_bias)) / cyan_bias, 0, 1)

    # emissive colour of a line pixel
    line_col = EMERALD[None, None, :]*(1-tfactor[..., None]) + ICE_CYAN[None, None, :]*tfactor[..., None]
    # white-hot core for the strongest strokes
    core_w = np.clip((line - 0.72)/0.28, 0, 1) * white_core
    line_col = line_col*(1-core_w[..., None]) + ICE_WHITE[None, None, :]*core_w[..., None]

    # --- void background with subtle tonal depth ----------------------------
    g = np.clip(gray, 0, 1) * void_depth
    void = VOID_DARK[None, None, :]*(1-g[..., None]) + VOID_LIGHT[None, None, :]*g[..., None]

    # composite
    result = void*(1-line[..., None]) + line_col*line[..., None]

    # --- restrained bioluminescent bloom -----------------------------------
    lum_map = line * (0.5 + 0.5*tfactor)          # brighter glow on cyan strokes
    lum_map = np.clip(lum_map, 0, 1)
    glow = cv2.GaussianBlur(lum_map, (0, 0), glow_sigma)[..., None]
    result = screen(result, glow, k=glow_amount)

    # global nebula vignette: darker at the very edge, gentle cool wash
    result = result * (1 - vignette_factor(result.shape[0], result.shape[1])[..., None])

    return from_float(result)


def vignette_factor(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w/2, h/2
    d = np.sqrt(((xx-cx)/(w*0.62))**2 + ((yy-cy)/(h*0.62))**2)
    vig = np.clip(d - 0.55, 0, 1) * 0.28
    return vig


def glacial_grade_tiled(img, params=None, strips=5, overlap=96):
    """Grouped tiled grade to bound peak memory on large images."""
    p = dict(params or {})
    H, W = img.shape[:2]
    sh = (H // strips) + 1
    out = np.empty((H, W, 3), dtype=np.uint8)
    us = img.astype(np.uint8)
    for i in range(strips):
        y0 = max(0, i*sh - (overlap if i > 0 else 0))
        y1 = min(H, (i+1)*sh + (overlap if i < strips-1 else 0))
        sub = glacial_grade(us[y0:y1], p)
        # keep only the inner region (drop overlap) then re-apply global vig
        a = i*sh if i > 0 else 0
        b = min(H, (i+1)*sh)
        inner = sub[(a-y0):(b-y0)]
        vig = vignette_factor(H, W)[a:b]
        inner = (inner.astype(np.float32) * (1 - vig[..., None]))
        out[a:b] = np.clip(inner, 0, 255).astype(np.uint8)
    return out


def desat_weight(rgb, lo=0.06, hi=0.30):
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    s = (maxc - minc) / (maxc + 1e-4)
    return np.clip((s - lo)/(hi - lo), 0, 1)


def hue_shift_red_to_accent(img, accent=ICE_CYAN, blend=0.85):
    """Rework saturated red/magenta ink accents into neon. Returns uint8 image."""
    f = to_float(img)
    rgb = f[..., :3]
    # redness: high R relative to G/B, moderately saturated
    rd = np.clip(rgb[...,0] - np.maximum(rgb[...,1], rgb[...,2]) , 0, 1)
    hotspot = np.clip(rd*3.0, 0, 1) * desat_weight(rgb)
    hotspot = cv2.GaussianBlur(hotspot, (0, 0), 5)[..., None]
    # tint to accent based on local luminance
    gray = (0.2126*rgb[...,0] + 0.7152*rgb[...,1] + 0.0722*rgb[...,2])[..., None]
    accent_col = ICE_CYAN[None,None,:]*(0.9) + ICE_WHITE[None,None,:]*0.1
    replaced = rgb*(1-hotspot) + accent_col*hotspot
    out = from_float(replaced)
    return cv2.convertScaleAbs(out, alpha=1.0, beta=0.0)
