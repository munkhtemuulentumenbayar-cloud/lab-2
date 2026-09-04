#!/usr/bin/env python3
"""Restore the 'glacial cable' (cyan/emerald bioluminescent cable glow) on
render 3, on top of the approved cinematic grade + detail boost."""
import cv2
from style_render import load_rgb_alpha, composite_on_void, CINEMATIC, detail_boost
from enhance import render_grade, cable_glow_sel

SRC = "render 3.png"
OUT = "renders/render 3.glacial-cable.png"

# cable glow params (tuned for a clear but controlled icy cable bloom)
GLOW = dict(amt=1.05, weight=0.62, bloom=11)

rgb, alpha = load_rgb_alpha(SRC)
comp = composite_on_void(rgb, alpha)
out = render_grade(comp, CINEMATIC)
out = detail_boost(out, comp, strength=0.85)
out = cable_glow_sel(out, GLOW)

bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
cv2.imwrite(OUT, bgr)
print(f"wrote {OUT}  {bgr.shape[1]}x{bgr.shape[0]}")
