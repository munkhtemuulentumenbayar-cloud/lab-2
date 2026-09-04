#!/usr/bin/env python3
"""Upscale the high-quality cinematic render 3 to 16K for print.

Pipeline: LapSRN_x8 super-resolution (8x) -> Lanczos to exact 16K -> light unsharp.
Saves both a high-quality JPEG (for GitHub/print) and a PNG (lossless).
"""
import os
import time
import cv2

SRC = "renders/render 3.cinematic.png"
OUT_JPG = "renders/render 3.16k.jpg"
OUT_PNG = "renders/render 3.16k.png"
W, H = 15360, 8640          # 16K UHD (16:9)


def mem_mb():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable"):
                return int(line.split()[1]) // 1024
    return -1


t0 = time.time()
print(f"available mem: {mem_mb()} MB", flush=True)

img = cv2.imread(SRC, cv2.IMREAD_COLOR)
assert img is not None, f"cannot read {SRC}"
print(f"loaded {SRC} {img.shape[1]}x{img.shape[0]} in {time.time()-t0:.1f}s", flush=True)

# 4x super-resolution (LapSRN models OOM in this sandbox; FSRCNN is light)
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel("models/FSRCNN_x4.pb")
sr.setModel("fsrcnn", 4)
t1 = time.time()
img4 = sr.upsample(img)
print(f"FSRCNN 4x -> {img4.shape[1]}x{img4.shape[0]} in {time.time()-t1:.1f}s "
      f"(mem {mem_mb()} MB)", flush=True)

# exact 16K via Lanczos
t2 = time.time()
img16 = cv2.resize(img4, (W, H), interpolation=cv2.INTER_LANCZOS4)
print(f"Lanczos -> {img16.shape[1]}x{img16.shape[0]} in {time.time()-t2:.1f}s "
      f"(mem {mem_mb()} MB)", flush=True)

# light unsharp mask for print crispness (uint8, memory-safe)
t3 = time.time()
blur = cv2.GaussianBlur(img16, (0, 0), 1.0)
img16 = cv2.addWeighted(img16, 1.35, blur, -0.35, 0)
print(f"sharpen in {time.time()-t3:.1f}s (mem {mem_mb()} MB)", flush=True)

t4 = time.time()
cv2.imwrite(OUT_JPG, img16, [cv2.IMWRITE_JPEG_QUALITY, 95])
print(f"JPEG: {OUT_JPG}  {os.path.getsize(OUT_JPG)//1024//1024} MB  "
      f"({time.time()-t4:.1f}s)", flush=True)

t5 = time.time()
cv2.imwrite(OUT_PNG, img16)
print(f"PNG : {OUT_PNG}  {os.path.getsize(OUT_PNG)//1024//1024} MB  "
      f"({time.time()-t5:.1f}s)", flush=True)

print(f"TOTAL {time.time()-t0:.1f}s", flush=True)
