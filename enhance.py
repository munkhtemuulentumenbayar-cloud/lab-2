"""
Arctic Lens 'Cyber-Glacial' grading functions (persistent module).
Used to regenerate deliverable sheets. Includes:
  - glacial_grade (from glacial.py) via import
  - wireframe_grade: contrast/DoG wireframe recovery for faint linework
  - render_grade: cinematic cold photographic grade
  - cable_glow_sel: selective cyan glow on thin cable structures
  - proto_grade: faceted-prototype grade (keeps interior subdivision lines + luminous fill)
"""
import numpy as np
import cv2
from glacial import glacial_grade, glacial_grade_tiled, to_float, from_float


def wireframe_grade(img, params=None):
    p = params or {}
    gain = p.get("gain", 18.0); dc = p.get("dc", 1.2)
    glow = p.get("glow", 6.0); ga = p.get("glow_amount", 0.5); gamma = p.get("gamma", 1.3)
    f = to_float(img); gray = (0.2126*f[..., 0] + 0.7152*f[..., 1] + 0.0722*f[..., 2])
    hi = cv2.GaussianBlur(gray, (0, 0), 1.6); lo = cv2.GaussianBlur(gray, (0, 0), 7.0)
    detail = hi - lo
    dark_lin = np.clip(-detail*dc, 0, None); light_ln = np.clip(detail*0.4, 0, None)
    lin = np.clip(dark_lin*1.0 + light_ln*0.5, 0, 1)*gain; lin = np.clip(lin, 0, 1)**gamma
    bold = np.clip((cv2.GaussianBlur(lin, (0, 0), 5.0)/(lin+1e-4) - 0.5)/0.5, 0, 1); t = bold
    CY = np.array([0.49, 0.92, 1.0]); EM = np.array([0.22, 1.0, 0.69]); WH = np.array([0.86, 0.97, 1.0])
    col = EM[None, None, :]*(1-t[..., None]) + CY[None, None, :]*t[..., None]
    core = np.clip((lin-0.7)/0.3, 0, 1)[..., None]*0.35
    col = col*(1-core) + WH[None, None, :]*core
    filled = np.clip(0.5-detail*2.0, 0, 1)*0.15
    bg = (0.03 + 0.05*filled[..., None])*np.array([0.6, 1.0, 1.2], dtype=np.float32)[None, None, :]
    out = bg + col*lin[..., None]
    glmap = cv2.GaussianBlur(lin, (0, 0), glow)[..., None]*ga
    out = 1 - (1-out)*(1-glmap)
    return from_float(out)


def render_grade(img, params=None):
    p = params or {}
    darken = p.get("darken", 0.70); desat = p.get("desat", 0.72); cool = p.get("cool", 1.0)
    fog = p.get("fog", 0.10); st = np.array(p.get("shadow_tint", [0.045, 0.085, 0.120]), dtype=np.float32)
    f = to_float(img); gray = (0.2126*f[..., 0] + 0.7152*f[..., 1] + 0.0722*f[..., 2]); g3 = gray[..., None]
    d = g3*(1-desat) + f*desat; d = d*darken; d = d/(1+0.45*d); d = d/(1.0/(1+0.45*0.30))
    shad = np.clip(1.35-gray*2.4, 0, 1)[..., None]; hi = np.clip((gray-0.72)/0.28, 0, 1)[..., None]
    fr, fg, fb = d[..., 0], d[..., 1], d[..., 2]
    f_b = np.clip(fb*(1+0.12*cool), 0, 1); f_r = np.clip(fr*(1-0.16*cool*(1-0.4*hi[..., 0])), 0, 1)
    f_g = np.clip(fg*(1-0.04*cool), 0, 1)
    f3 = np.stack([f_r, f_g, f_b], -1); f3 = f3*(1-shad) + st[None, None, :]*shad
    if fog > 0:
        w = np.clip(1-np.abs(gray-0.55)*2.0, 0, 1)[..., None]
        f3 = f3*(1-fog*w) + np.array([0.14, 0.19, 0.24], dtype=np.float32)*fog*w
    return from_float(f3)


def cable_glow_sel(img, params=None):
    p = params or {}
    amt = p.get("amt", 1.25); weight = p.get("weight", 0.82); bloom = p.get("bloom", 12)
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)/255.0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    opened = cv2.morphologyEx(g, cv2.MORPH_OPEN, k)
    thin = np.clip(g-opened, 0, 1)
    bright = (g > 0.48).astype(np.uint8)
    kern = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    eroded = cv2.erode(bright, kern)
    largeblob = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    largeblob = cv2.GaussianBlur(largeblob.astype(np.float32), (0, 0), 6)
    m = np.clip(thin, 0, 1)*(1-largeblob); m = np.clip(m*3.0, 0, 1); m = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
    cyan = np.array([0.49, 0.92, 1.0]); ecy = np.array([0.22, 1.0, 0.69])
    col = cv2.GaussianBlur((m)*amt, (0, 0), bloom)[..., None]
    f = to_float(img)
    out = f*(1-m*weight) + (cyan*0.9 + ecy*0.1)*m*weight
    out = 1 - (1-out)*(1-col)
    return from_float(out)


def proto_grade(img, params=None):
    p = params or {}
    gain = p.get("gain", 20.0); gamma = p.get("gamma", 1.25)
    glow = p.get("glow", 5.0); ga = p.get("glow_amount", 0.32); fill = p.get("fill", 0.18)
    f = to_float(img); gray = (0.2126*f[..., 0] + 0.7152*f[..., 1] + 0.0722*f[..., 2])
    d1 = cv2.GaussianBlur(gray, (0, 0), 1.2) - cv2.GaussianBlur(gray, (0, 0), 4.0)
    d2 = cv2.GaussianBlur(gray, (0, 0), 3.0) - cv2.GaussianBlur(gray, (0, 0), 9.0)
    detail = d1 + 0.5*d2
    lin = np.clip(np.abs(detail)*gain*1.6, 0, 1)**gamma
    bold = np.clip((cv2.GaussianBlur(lin, (0, 0), 4.0)/(lin+1e-4) - 0.5)/0.5, 0, 1)
    CY = np.array([0.49, 0.92, 1.0]); EM = np.array([0.22, 1.0, 0.69]); WH = np.array([0.9, 0.98, 1.0])
    col = EM[None, None, :]*(1-bold[..., None]) + CY[None, None, :]*bold[..., None]
    core = np.clip((lin-0.85)/0.15, 0, 1)[..., None]*0.35
    col = col*(1-core) + WH[None, None, :]*core
    grad = cv2.GaussianBlur(np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)) +
                            np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)), (0, 0), 2)
    flatpx = np.clip(1.0-grad*8.0, 0, 1)
    fillmask = np.clip((gray-0.35)/0.25, 0, 1)*np.clip((0.92-gray)/0.3, 0, 1)
    facetfill = flatpx*fillmask*fill
    bg = (0.03 + 0.06*facetfill[..., None])*np.array([0.7, 1.0, 1.15], dtype=np.float32)[None, None, :]
    out = bg + col*lin[..., None] + facetfill[..., None]*np.array([0.30, 0.70, 0.85], dtype=np.float32)[None, None, :]*0.5
    glmap = cv2.GaussianBlur(lin, (0, 0), glow)[..., None]*ga
    out = 1 - (1-out)*(1-glmap)
    return from_float(out)


def vignette_factor(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w/2, h/2
    d = np.sqrt(((xx-cx)/(w*0.62))**2 + ((yy-cy)/(h*0.62))**2)
    return np.clip(d - 0.55, 0, 1) * 0.28
