#!/usr/bin/env python3
"""THE ARCTIC LENS — exam drawing set
Seven 900 x 900 mm sheets in one DXF (model-space composition + paper layouts).
Units: millimetres. Plot each layout 1:1 on 90 x 90 cm.
Author: Munkhtemuulen Tumenbayar — UNIUD DPIA — 2026
"""
from __future__ import annotations

import math
import os
from copy import deepcopy

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from ezdxf.lldxf.const import LWPOLYLINE_CLOSED
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "TAVOLE_ESAME_90x90.dxf")

SHEET = 900.0
GAP = 200.0
MARGIN = 10.0
TOP = 46.0
BOT = 24.0

# programme colours (RGB)
COL = {
    "R": (70, 145, 210),
    "L": (232, 140, 50),
    "H": (230, 130, 170),
    "E": (170, 195, 70),
    "C": (160, 165, 170),
    "V": (235, 170, 45),
    "CIRC": (210, 55, 55),
    "NAVY": (20, 32, 48),
    "INK": (32, 36, 42),
    "MUTED": (90, 98, 108),
    "RULE": (180, 186, 192),
    "FJORD": (150, 190, 210),
    "ROCK": (168, 172, 176),
    "PAPER": (248, 249, 250),
    "AMBER": (245, 236, 214),
    "PINKBG": (252, 236, 236),
    "BLUEBG": (232, 240, 248),
}

# 32-cell register — 4 clusters + civic + 4 voids = 32
# Research 7 labs + V01 = 8
# Logistics 8
# Habitat 7 + V02 = 8
# Eco 4 + V03 = 5
# Civic 2 + V04 = 3
PODS = [
    # RESEARCH
    ("L01", "R", "Offices"),
    ("L02", "R", "Observation"),
    ("L03", "R", "Dry lab"),
    ("L04", "R", "IT / server"),
    ("L05", "R", "Collaboration"),
    ("L06", "R", "Wet lab A"),
    ("L07", "R", "Wet lab B"),
    ("V01", "V", "Sky observatory / wind"),
    # LOGISTICS
    ("T01", "L", "Workshop"),
    ("T02", "L", "Isolation"),
    ("T03", "L", "Infirmary"),
    ("T04", "L", "Heat-pump"),
    ("T05", "L", "Water / waste"),
    ("T06", "L", "Comms"),
    ("T07", "L", "ER / trauma"),
    ("T08", "L", "Stores"),
    # HABITAT
    ("R01", "H", "Gym"),
    ("R02", "H", "Sauna + plunge"),
    ("R03", "H", "Quiet / therapy"),
    ("R04", "H", "Suites"),
    ("R05", "H", "Lounge"),
    ("R06", "H", "Cabins A"),
    ("R07", "H", "Cabins B"),
    ("V02", "V", "Aurora deck / solar"),
    # ECO
    ("E01", "E", "Cold store"),
    ("E02", "E", "Hydroponics"),
    ("E03", "E", "Aquaponics"),
    ("E04", "E", "Greenhouse"),
    ("V03", "V", "Light-well / store"),
    # CIVIC
    ("C01", "C", "Dining / assembly"),
    ("C02", "C", "Sanctuary / time"),
    ("V04", "V", "Oculus / drone deck"),
]
assert len(PODS) == 32

# truncated octahedron
EDGE_M = 4.2
# hex floor: opposite-hex distance ~ 10.29 m; nominal plan width 10.8 m internal
PLAN_FF = 10800.0  # flat-to-flat mm
PLAN_R = PLAN_FF / math.sqrt(3)  # circumradius mm
CC = PLAN_FF  # centre-centre of face-sharing hexes


def rgb(t):
    return t


def sheet_origin(i):
    col, row = i % 4, i // 4
    return col * (SHEET + GAP), -row * (SHEET + GAP)


def hex_pts(cx, cy, r, n=6, rot=math.radians(30)):
    """flat-top hexagon if rot=30°."""
    return [
        (cx + r * math.cos(rot + i * math.pi / 3),
         cy + r * math.sin(rot + i * math.pi / 3))
        for i in range(n)
    ]


def neighbor_xy(cx, cy, k, dist=CC):
    a = math.radians(60 * k)
    return cx + dist * math.cos(a), cy + dist * math.sin(a)


class CAD:
    def __init__(self):
        self.doc = ezdxf.new("R2018", setup=True)
        self.doc.units = units.MM
        self.doc.header["$INSUNITS"] = 4
        self.doc.header["$LUNITS"] = 2
        self.doc.header["$LWDISPLAY"] = 1
        self._layers()
        self._styles()
        self.msp = self.doc.modelspace()
        self.image_defs = {}

    def _layers(self):
        layers = {
            "A-SHEET": (COL["NAVY"], 50),
            "A-TITL": (COL["NAVY"], 35),
            "A-ANNO": (COL["INK"], 18),
            "A-DIM": (COL["MUTED"], 13),
            "A-WALL": (COL["INK"], 40),
            "A-FURN": (COL["MUTED"], 18),
            "A-HATCH": (COL["RULE"], 9),
            "P-R": (COL["R"], 25),
            "P-L": (COL["L"], 25),
            "P-H": (COL["H"], 25),
            "P-E": (COL["E"], 25),
            "P-C": (COL["C"], 25),
            "P-V": (COL["V"], 25),
            "S-CABLE": (COL["INK"], 30),
            "C-SEA": (COL["FJORD"], 25),
            "C-ROAD": ((140, 90, 45), 25),
            "C-AIR": ((200, 60, 120), 25),
            "A-RENDER": (COL["INK"], 0),
            "A-TABLE": (COL["INK"], 13),
            "G-GRID": ((210, 214, 218), 9),
        }
        for name, (c, lw) in layers.items():
            layer = self.doc.layers.add(name)
            layer.rgb = c
            layer.dxf.lineweight = lw

    def _styles(self):
        for n, f in (("TITLE", "Arial.ttf"), ("ANNO", "Arial.ttf"), ("ISO", "Arial.ttf")):
            if n not in self.doc.styles:
                self.doc.styles.add(n, font=f)

    def mtext(self, x, y, text, h=2.5, w=80, layer="A-ANNO", bold=False, align="LEFT", rgb_=None, color=None):
        ha = {"LEFT": 1, "CENTER": 2, "RIGHT": 3}.get(align, 1)
        att = {
            "layer": layer,
            "char_height": h,
            "width": w,
            "style": "TITLE" if bold else "ANNO",
            "attachment_point": ha if align != "LEFT" else 1,
            "insert": (x, y),
            "color": 7,
        }
        t = text
        e = self.msp.add_mtext(t, dxfattribs=att)
        if rgb_:
            e.rgb = rgb_
        else:
            e.rgb = COL["NAVY"] if bold else COL["INK"]
        return e

    def line(self, a, b, layer="A-ANNO", rgb_=None, lw=None):
        e = self.msp.add_line(a, b, dxfattribs={"layer": layer})
        if rgb_:
            e.rgb = rgb_
        if lw is not None:
            e.dxf.lineweight = lw
        return e

    def pline(self, pts, layer="A-WALL", close=True, rgb_=None, lw=None):
        e = self.msp.add_lwpolyline(
            pts, format="xy",
            dxfattribs={"layer": layer, "closed": close},
        )
        if rgb_:
            e.rgb = rgb_
        if lw is not None:
            e.dxf.lineweight = lw
        return e

    def circle(self, c, r, layer="A-ANNO", rgb_=None):
        e = self.msp.add_circle(c, r, dxfattribs={"layer": layer})
        if rgb_:
            e.rgb = rgb_
        return e

    def solid_hatch(self, pts, rgb_, layer="A-HATCH"):
        h = self.msp.add_hatch(color=7, dxfattribs={"layer": layer})
        h.rgb = rgb_
        h.set_solid_fill()
        h.paths.add_polyline_path([(p[0], p[1]) for p in pts], is_closed=True)
        return h

    def rect(self, x, y, w, h, layer="A-SHEET", rgb_=None, fill=None, lw=None):
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        if fill:
            self.solid_hatch(pts, fill, layer="A-HATCH")
        return self.pline(pts, layer=layer, rgb_=rgb_, lw=lw)

    def image(self, filename, insert, size):
        path = filename if os.path.isabs(filename) else os.path.join(ASSETS, filename)
        if not os.path.exists(path):
            self.rect(insert[0], insert[1], size[0], size[1], layer="A-RENDER", rgb_=COL["RULE"])
            self.mtext(insert[0] + 4, insert[1] + size[1] - 8, os.path.basename(path), h=2.2, w=size[0] - 8)
            return
        key = os.path.abspath(path)
        if key not in self.image_defs:
            im = Image.open(path)
            self.image_defs[key] = self.doc.add_image_def(
                filename=os.path.relpath(path, HERE),
                size_in_pixel=(im.size[0], im.size[1]),
            )
        self.msp.add_image(
            image_def=self.image_defs[key],
            insert=insert,
            size_in_units=size,
            dxfattribs={"layer": "A-RENDER"},
        )

    def north(self, x, y, s=14):
        pts = [(x, y + s), (x - s * 0.28, y - s * 0.45), (x, y - s * 0.1), (x + s * 0.28, y - s * 0.45)]
        self.solid_hatch(pts[:3], COL["NAVY"])
        self.pline(pts, layer="A-ANNO", rgb_=COL["NAVY"], lw=20)
        self.mtext(x - 4, y + s + 2, "N", h=3, w=12, bold=True, align="CENTER")

    def scalebar(self, x, y, paper_len, real_m, label):
        self.line((x, y), (x + paper_len, y), layer="A-DIM", rgb_=COL["INK"], lw=25)
        self.line((x, y - 1.5), (x, y + 1.5), layer="A-DIM", rgb_=COL["INK"], lw=25)
        self.line((x + paper_len, y - 1.5), (x + paper_len, y + 1.5), layer="A-DIM", rgb_=COL["INK"], lw=25)
        self.mtext(x, y + 3, f"0", h=1.8, w=20)
        self.mtext(x + paper_len - 10, y + 3, f"{real_m:g} m", h=1.8, w=30)
        self.mtext(x, y - 6, label, h=1.8, w=60, rgb_=COL["MUTED"])

    def frame(self, ox, oy, n, title, subtitle, scales):
        # outer
        self.rect(ox, oy, SHEET, SHEET, layer="A-SHEET", rgb_=COL["NAVY"], lw=70)
        self.rect(ox + 4, oy + 4, SHEET - 8, SHEET - 8, layer="A-SHEET", rgb_=COL["NAVY"], lw=25)
        # top bar
        self.rect(ox + 4, oy + SHEET - 4 - TOP, SHEET - 8, TOP, fill=COL["NAVY"], layer="A-TITL")
        self.mtext(ox + 14, oy + SHEET - 18, "THE ARCTIC LENS", h=4.2, w=200, bold=True, rgb_= (255,255,255), layer="A-TITL")
        self.mtext(ox + 14, oy + SHEET - 32, f"TAVOLA {n}/7  ·  {title}", h=6.2, w=620, bold=True, rgb_=(255,255,255), layer="A-TITL")
        self.mtext(ox + 14, oy + SHEET - 44, subtitle, h=2.4, w=700, rgb_=(200, 210, 220), layer="A-TITL")
        self.mtext(ox + SHEET - 160, oy + SHEET - 20, "900 × 900 mm", h=2.4, w=140, rgb_=(200,210,220), layer="A-TITL")
        # bottom bar
        self.rect(ox + 4, oy + 4, SHEET - 8, BOT, fill=COL["NAVY"], layer="A-TITL")
        self.mtext(ox + 14, oy + 12, "UNIUD  ·  DPIA  ·  Master’s Degree in Architecture", h=2.2, w=420, rgb_=(255,255,255), layer="A-TITL")
        self.mtext(ox + 430, oy + 12, "Munkhtemuulen Tumenbayar  ·  A.Y. 2025/26  ·  Lofoten  68.22°N 13.56°E", h=2.2, w=360, rgb_=(255,255,255), layer="A-TITL")
        self.mtext(ox + SHEET - 130, oy + 12, scales, h=2.2, w=120, rgb_=(255,255,255), layer="A-TITL")
        return ox + 14, oy + 36, SHEET - 28, SHEET - TOP - BOT - 20

    def panel(self, x, y, w, h, caption=None, fill=None):
        self.rect(x, y, w, h, layer="A-SHEET", rgb_=COL["RULE"], fill=fill or (252, 253, 254), lw=13)
        if caption:
            self.mtext(x + 3, y + h - 6, caption, h=2.2, w=w - 6, bold=True, rgb_=COL["NAVY"])

    def table(self, x, y, w, rows, row_h=5.4, header=True):
        cols = len(rows[0])
        cw = [w * r for r in ([0.18, 0.22, 0.60] if cols == 3 else [1 / cols] * cols)]
        if cols == 4:
            cw = [w * 0.16, w * 0.22, w * 0.22, w * 0.40]
        if cols == 2:
            cw = [w * 0.34, w * 0.66]
        yy = y
        for i, row in enumerate(rows):
            xx = x
            bg = COL["NAVY"] if (header and i == 0) else (COL["AMBER"] if i % 2 == 0 else (255, 255, 255))
            self.rect(x, yy - row_h, w, row_h, fill=bg, rgb_=COL["RULE"], lw=9)
            for j, cell in enumerate(row):
                col = (255, 255, 255) if (header and i == 0) else COL["INK"]
                self.mtext(xx + 1.5, yy - row_h + 1.4, str(cell), h=1.7, w=cw[j] - 2, rgb_=col, layer="A-TABLE")
                xx += cw[j]
            yy -= row_h
        return yy

    def truncated_oct_2d(self, cx, cy, s, layer="A-WALL"):
        """schematic 2d truncated octahedron (hex + cuts)."""
        r = s
        pts = hex_pts(cx, cy, r)
        self.pline(pts, layer=layer, rgb_=COL["INK"], lw=35)
        inner = hex_pts(cx, cy, r * 0.58, rot=0)
        self.pline(inner, layer=layer, rgb_=COL["MUTED"], lw=18)
        for a, b in zip(pts, pts[1:] + pts[:1]):
            self.line(a, (cx, cy), layer="G-GRID", rgb_=(200, 205, 210), lw=9)
        return pts


# ---------------------------------------------------------------------------
# settlement geometry in WORLD millimetres
# ---------------------------------------------------------------------------
def cluster_world():
    """Return dict id -> (x,y) world mm, plus group centres."""
    R = PLAN_R
    d = CC

    def flower(cx, cy, extra_k=None):
        pts = [(cx, cy)]
        for k in range(6):
            pts.append(neighbor_xy(cx, cy, k, d))
        if extra_k is not None:
            # extra attached to neighbor extra_k
            nx, ny = pts[1 + extra_k]
            pts.append(neighbor_xy(nx, ny, extra_k, d))
        return pts

    pos = {}
    # civic pair at origin
    pos["C01"] = (0, 0)
    pos["C02"] = (d, 0)
    pos["V04"] = (d * 0.5, -d * 0.88)

    # research NW
    rcx, rcy = -52000, 38000
    rp = flower(rcx, rcy, extra_k=3)
    ids_r = ["L04", "L01", "L02", "L03", "L05", "L06", "L07", "V01"]
    for i, pid in enumerate(ids_r):
        pos[pid] = rp[i]

    # logistics NE
    lcx, lcy = 52000, 38000
    lp = flower(lcx, lcy, extra_k=0)
    ids_l = ["T04", "T01", "T02", "T03", "T05", "T06", "T07", "T08"]
    for i, pid in enumerate(ids_l):
        pos[pid] = lp[i]

    # habitat SW
    hcx, hcy = -52000, -40000
    hp = flower(hcx, hcy, extra_k=4)
    ids_h = ["R05", "R01", "R02", "R03", "R04", "R06", "R07", "V02"]
    for i, pid in enumerate(ids_h):
        pos[pid] = hp[i]

    # eco SE — 5 cells
    ecx, ecy = 52000, -40000
    ep = [(ecx, ecy)]
    for k in range(4):
        ep.append(neighbor_xy(ecx, ecy, k, d))
    ids_e = ["E02", "E01", "E03", "E04", "V03"]
    for i, pid in enumerate(ids_e):
        pos[pid] = ep[i]

    return pos


POD_POS = cluster_world()
POD_MAP = {p[0]: p for p in PODS}


def draw_settlement(cad: CAD, ox, oy, scale, draw_ids=True, fill=True, r_paper=None):
    """Draw cluster plan onto sheet. world mm / scale = paper mm."""
    def P(xy):
        return ox + xy[0] / scale, oy + xy[1] / scale

    r_w = PLAN_R
    r_p = r_w / scale if r_paper is None else r_paper
    # bridges civic to clusters
    civic = P(POD_POS["C01"])
    for pid in ("L04", "T04", "R05", "E02"):
        a, b = civic, P(POD_POS[pid])
        cad.line(a, b, layer="A-WALL", rgb_=(90, 100, 110), lw=40)
    # ring
    ring = ["L05", "T07", "E04", "R06"]
    rp = [P(POD_POS[i]) for i in ring if i in POD_POS]
    if len(rp) >= 2:
        cad.pline(rp, close=True, layer="P-V", rgb_=COL["CIRC"], lw=20)

    for pid, grp, name in PODS:
        x, y = P(POD_POS[pid])
        pts = hex_pts(x, y, r_p)
        col = COL[grp]
        if fill:
            fill_c = tuple(min(255, int(c + (255 - c) * 0.55)) for c in col)
            cad.solid_hatch(pts, fill_c)
        cad.pline(pts, layer=f"P-{grp}", rgb_=col, lw=30 if grp != "V" else 25)
        if grp == "V":
            inner = hex_pts(x, y, r_p * 0.72)
            cad.pline(inner, layer="P-V", rgb_=col, lw=13)
        if draw_ids:
            cad.mtext(x - r_p * 0.7, y + r_p * 0.15, pid, h=max(1.6, r_p * 0.18), w=r_p * 1.4, bold=True, align="CENTER", rgb_=COL["NAVY"])
            cad.mtext(x - r_p * 0.85, y - r_p * 0.35, name, h=max(1.3, r_p * 0.12), w=r_p * 1.7, align="CENTER", rgb_=COL["INK"])
    # terminal mark
    tx, ty = P((0, -18000))
    cad.circle((tx, ty), 4.5, layer="A-ANNO", rgb_=COL["NAVY"])
    cad.solid_hatch(hex_pts(tx, ty, 3, n=8), COL["NAVY"])
    cad.mtext(tx + 6, ty - 2, "TERMINAL + ASCENT CORE", h=2.0, w=70, rgb_=COL["NAVY"])
    # helipad
    hx, hy = P((8000, 72000))
    cad.circle((hx, hy), 7, layer="C-AIR", rgb_=COL["CIRC"])
    cad.mtext(hx - 4, hy - 1.5, "H", h=3.2, w=12, bold=True, rgb_=COL["CIRC"])
    cad.mtext(hx + 9, hy - 1, "SUMMIT HELIPAD", h=2.0, w=50, rgb_=COL["CIRC"])
    cad.line((hx, hy), P((0, 0)), layer="C-AIR", rgb_=COL["CIRC"], lw=13)


# ===========================================================================
# BOARDS
# ===========================================================================

def board_01(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 1, "CONCEPT & TERRITORY",
                           "why suspend here  ·  unit → field  ·  Lofoten insertion",
                           "1:7500  ·  1:500")
    # concept strip
    cad.panel(x, y + 8, 118, h - 20, "CONCEPT  ·  5 STEPS")
    steps = [
        "1  ELEMENTAL UNIT\nTruncated octahedron\nedge 4.2 m",
        "2  BINARY JOIN\nØ 3.6 m portal\nshared hex face",
        "3  NUCLEUS\nthree cells\nstable pack",
        "4  WIND VOIDS\n4 open frames\nporosity",
        "5  TENSION NET\nØ 85 mm cables\n48 rock anchors",
    ]
    for i, t in enumerate(steps):
        cy = y + h - 70 - i * 145
        cad.rect(x + 14, cy, 90, 110, rgb_=COL["RULE"], fill=(255, 255, 255))
        cad.truncated_oct_2d(x + 59, cy + 62, 22 - i * 0.5)
        if i >= 1:
            cad.truncated_oct_2d(x + 78, cy + 50, 16)
        cad.mtext(x + 18, cy + 8, t, h=2.0, w=82, rgb_=COL["INK"])

    # site plan
    cad.panel(x + 128, y + h - 430, 520, 422, "SITE PLAN  ·  CONNECTION TO THE WORLD  ·  SCALE 1:7500")
    cad.image("site_connections.png", (x + 136, y + h - 422), (504, 288))
    cad.north(x + 620, y + h - 160, 12)
    cad.scalebar(x + 150, y + h - 425 + 8, 40, 300, "SCALE 1:7500  (40 mm = 300 m)")

    cad.mtext(x + 136, y + h - 430 + 18,
              "Three routes, one gate. Sea (pier + cable-car) · Road (E10 tunnel) · Air (summit helipad on rock).\n"
              "All meet at the Terminal hidden in the granite. Nothing is built on the shore.",
              h=2.1, w=500, rgb_=COL["INK"])

    # hero
    cad.panel(x + 128, y + 8, 520, h - 448, "HERO  ·  SUSPENDED FIELD OVER THE FJORD")
    cad.image("GENDO_NORWAY_8EC8.png", (x + 136, y + 16), (340, 300))
    cad.image("render_cable_hi2.png", (x + 484, y + 80), (156, 94))
    cad.mtext(x + 484, y + 20, "Cable field  ·  glacial light\nZero ground footprint\nProposed suspension +22.00 m", h=2.0, w=155)

    # locator / notes
    cad.panel(x + 656, y + 8, w - 656, h - 20, "TERRITORY")
    cad.mtext(x + 664, y + h - 80,
              "SITE\nBunesfjorden\nMoskenesøya\nLofoten, Norway\n68.22°N  13.56°E\n\n"
              "DATUM\nFjord SWL = +0.00\n(site datum)\n\n"
              "ETHIC\nZero-trace objective:\nhang, do not found.\n48 removable anchors.\n\n"
              "CLIMATE (Met.no)\nWind 42 m/s SW\nWinter −20 °C\nMidnight sun / aurora\n\n"
              "PROTECTION\nLophelia pertusa\nNaturmangfoldloven\nFloating pier only.",
              h=2.3, w=130, rgb_=COL["INK"])


def board_02(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 2, "ARRIVAL & THRESHOLDS",
                           "how a person reaches the habitat  ·  sea / road / air  ·  medevac line",
                           "1:500  ·  1:200")
    # site
    cad.panel(x, y + h - 268, 430, 260, "TERRITORIAL PLAN  ·  ARRIVALS  ·  1:7500")
    cad.image("site_connections.png", (x + 8, y + h - 260), (414, 236))

    cad.panel(x + 438, y + h - 268, w - 438, 260, "HOW IT WORKS  ·  FOUR STEPS")
    cad.image("how_it_works.png", (x + 446, y + h - 260), (250, 250))
    steps = [
        "1 ARRIVE  sea / road / air",
        "2 TERMINAL  only gate, in the rock",
        "3 ASCENT CORE  lift + stair",
        "4 CIVIC HEART  main square",
    ]
    cad.mtext(x + 700, y + h - 40, "\n".join(steps), h=2.4, w=160)

    # section — CAD redrawn at 1:500
    cad.panel(x, y + 210, w, h - 488, "TERRITORIAL SECTION  ·  FJORD → PIER → TERMINAL → CORE → SETTLEMENT → HELIPAD  ·  1:500  (proposed datums)")
    draw_arrival_section(cad, x + 20, y + 230, 1 / 500.0)

    # medical + terminal
    cad.panel(x, y + 8, 430, 194, "MEDEVAC  ·  ONE VERTICAL LINE (IN ROCK)")
    cad.image("section_circulation.png", (x + 8, y + 14), (180, 180))
    cad.mtext(x + 196, y + 150,
              "Helipad on SOLID ROCK (not on the cables).\n"
              "Express lift: helipad ↔ terminal.\n"
              "ER / infirmary at Ascent Core, short bridge.\n"
              "Stretcher does not cross the hanging ring in storm.\n"
              "V4 drone deck serves the settlement itself.\n\n"
              "NOTE  The hanging ER cannot sit inside the rock shaft.\n"
              "Draw the transfer landing at bridge level; the shaft\n"
              "is the rock-side express lift. Proposed — verify survey.",
              h=2.05, w=225)

    cad.panel(x + 438, y + 8, w - 438, 194, "TERMINAL  ·  BASE CAMP  ·  1:200 schematic")
    draw_terminal_plan(cad, x + 460, y + 20)


def draw_arrival_section(cad: CAD, x, y, sc):
    """sc = paper_mm / world_mm. 1:500 => 0.002. World in mm."""
    # use metres * sc * 1000
    def X(m):
        return x + m * 1000 * sc
    def Y(m):
        return y + m * 1000 * sc

    # water
    cad.solid_hatch([(X(-20), Y(-8)), (X(90), Y(-8)), (X(90), Y(0)), (X(-20), Y(0))], COL["FJORD"])
    cad.mtext(X(-18), Y(-6), "FJORD  SWL +0.00", h=2.2, w=50, rgb_=(20, 70, 90), bold=True)
    # pier
    cad.rect(X(8), Y(0), (14) * 1000 * sc, 1.5 * 1000 * sc, fill=(40, 80, 100), rgb_=(40, 80, 100))
    cad.mtext(X(8), Y(3), "floating pier", h=1.8, w=40)
    # mountain
    rock = [(X(95), Y(-8)), (X(200), Y(-8)), (X(200), Y(120)), (X(150), Y(110)), (X(128), Y(95)),
            (X(118), Y(55)), (X(110), Y(28)), (X(100), Y(8)), (X(95), Y(0))]
    cad.solid_hatch(rock, (190, 194, 198))
    cad.pline(rock, layer="A-WALL", rgb_=(110, 115, 120), lw=25, close=False)
    # terminal
    cad.rect(X(112), Y(28), 18 * 1000 * sc, 8 * 1000 * sc, fill=(255, 255, 255), rgb_=COL["NAVY"], lw=30)
    cad.mtext(X(114), Y(31.5), "TERMINAL  +32.00", h=2.0, w=50, bold=True)
    # tunnel
    cad.line((X(130), Y(32)), (X(175), Y(32)), layer="C-ROAD", rgb_=(140, 90, 45), lw=40)
    cad.mtext(X(150), Y(34), "E10 tunnel", h=1.8, w=40, rgb_=(140, 90, 45))
    # helipad
    cad.rect(X(126), Y(94), 16 * 1000 * sc, 1.2 * 1000 * sc, fill=COL["CIRC"], rgb_=COL["CIRC"])
    cad.circle((X(134), Y(97)), 4, layer="C-AIR", rgb_=COL["CIRC"])
    cad.mtext(X(136), Y(97), "H  HELIPAD  +95.00 proposed", h=2.0, w=70, rgb_=COL["CIRC"], bold=True)
    # express lift
    cad.rect(X(132.5), Y(36), 2.2 * 1000 * sc, 58 * 1000 * sc, fill=(255, 210, 210), rgb_=COL["CIRC"], lw=20)
    cad.mtext(X(135.2), Y(60), "express / medevac lift", h=1.8, w=40, rgb_=COL["CIRC"])
    # settlement
    for i, (dx, col) in enumerate([(-38, COL["R"]), (-26, COL["C"]), (-14, COL["L"]), (-2, COL["H"])]):
        px, py = X(70 + dx), Y(22)
        cad.pline(hex_pts(px, py + 8, 7), layer="A-WALL", rgb_=col, lw=20)
        cad.solid_hatch(hex_pts(px, py + 8, 7), tuple(min(255, c + 40) for c in col))
    cad.mtext(X(28), Y(40), "SUSPENDED SETTLEMENT", h=2.1, w=70, bold=True)
    cad.mtext(X(28), Y(18), "soffit +22.00  ·  main deck +25.50  ·  apex ~ +32.3", h=1.7, w=90)
    # cables
    for dx in range(0, 8):
        cad.line((X(40 + dx * 4), Y(30)), (X(118), Y(70 + dx * 2)), layer="S-CABLE", rgb_=(80, 90, 100), lw=13)
    # ascent core diagonal
    cad.line((X(112), Y(36)), (X(78), Y(26)), layer="C-SEA", rgb_=(40, 130, 170), lw=35)
    cad.mtext(X(88), Y(33), "Ascent Core (lift + stair)", h=1.8, w=55, rgb_=(40, 130, 170))
    # cable-car
    cad.line((X(15), Y(2)), (X(112), Y(32)), layer="C-SEA", rgb_=(40, 130, 170), lw=18)
    cad.mtext(X(40), Y(10), "cable-car (by sea)", h=1.8, w=50, rgb_=(40, 130, 170))
    # ER
    cad.pline(hex_pts(X(92), Y(30), 6), layer="P-L", rgb_=COL["L"], lw=20)
    cad.mtext(X(86), Y(24), "ER + INFIRMARY", h=1.7, w=40, rgb_=COL["CIRC"], bold=True)
    # datums
    for zm, lab in [(0, "+0.00 SWL"), (22, "+22.00 soffit"), (32, "+32.00 terminal"), (95, "+95.00 helipad")]:
        cad.line((X(178), Y(zm)), (X(188), Y(zm)), layer="A-DIM", rgb_=COL["MUTED"], lw=13)
        cad.mtext(X(188.5), Y(zm) - 1, lab, h=1.7, w=40, rgb_=COL["MUTED"])
    cad.mtext(X(-18), Y(108), "Proposed vertical sequence — not a surveyed section. 45 m core is the brief parameter; fit to cliff is a study.", h=1.7, w=220, rgb_=COL["MUTED"])


def draw_terminal_plan(cad: CAD, x, y):
    cad.rect(x, y, 240, 160, rgb_=COL["NAVY"], fill=(245, 246, 247), lw=20)
    rooms = [
        (8, 90, 70, 60, "RECEPTION"),
        (82, 90, 70, 60, "DRY ROOM\nBASE CAMP"),
        (156, 90, 76, 60, "CARGO /\nCOLD STORE"),
        (8, 10, 70, 70, "E10\nTUNNEL"),
        (82, 10, 70, 70, "CABLE-CAR\nARRIVAL"),
        (156, 10, 76, 70, "ASCENT CORE\n+ EXPRESS LIFT"),
    ]
    for rx, ry, rw, rh, t in rooms:
        cad.rect(x + rx, y + ry, rw, rh, rgb_=COL["INK"], fill=(255, 255, 255), lw=18)
        cad.mtext(x + rx + 4, y + ry + rh / 2 - 4, t, h=2.0, w=rw - 6, rgb_=COL["NAVY"])
    cad.mtext(x + 8, y + 168, "Single public gate. Fire / storm orientation is unambiguous.", h=1.8, w=230, rgb_=COL["MUTED"])


def board_03(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 3, "SETTLEMENT & PROGRAMME",
                           "how 120 people inhabit 32 cells  ·  numbered register  ·  +3.50 m deck",
                           "1:500  ·  1:200")
    cad.panel(x, y + 210, 620, h - 218, "MASTERPLAN  ·  FOUR CLUSTERS + CIVIC HEART  ·  1:500")
    # draw settlement at 1:500, centred
    draw_settlement(cad, x + 310, y + 470, scale=500, draw_ids=True)
    cad.north(x + 24, y + h - 50, 12)
    cad.scalebar(x + 20, y + 220, 40, 20, "1:500   40 mm = 20 m")

    cad.panel(x + 628, y + 210, w - 628, h - 218, "POD REGISTER  ·  32 CELLS")
    rows = [["ID", "GRP", "PRIMARY USE"]]
    for pid, grp, name in PODS:
        rows.append([pid, grp, name])
    cad.table(x + 636, y + h - 40, w - 656, rows, row_h=5.15)

    cad.panel(x, y + 8, w, 194, "PROGRAMME  ·  120 INHABITANTS  ·  ROUTES")
    cad.table(x + 10, y + 185, 420, [
        ["CLUSTER", "CELLS", "ROLE"],
        ["Research (blue)", "L01–L07 + V01", "labs, observation, data"],
        ["Logistics (orange)", "T01–T08", "ER, plant, workshop, water"],
        ["Habitat (pink)", "R01–R07 + V02", "sleep, wellness, lounge"],
        ["Eco (green)", "E01–E04 + V03", "food, light-well"],
        ["Civic (grey)", "C01–C02 + V04", "assembly, sanctuary, oculus"],
    ], row_h=6.0)
    cad.mtext(x + 450, y + 150,
              "COLOUR is orientation in white-out and polar night.\n"
              "Grey spokes = enclosed bridges to Civic Heart.\n"
              "Red ring = second way out between clusters.\n"
              "Each cluster has a vertical core (lift + stair).\n\n"
              "OCCUPANCY TEST  120 residents. Sleeping is in Habitat\n"
              "(R04 suites + R06/R07 cabins). Board 5 fits 8 berths\n"
              "in one cabin pod. If 10 berths/pod × 12 pods is required,\n"
              "Habitat must grow or population must drop — see table.\n"
              "Do not hide this. It is a design finding.",
              h=2.05, w=400)


def board_04(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 4, "SUSPENSION & ASSEMBLY",
                           "how the field is held, connected and removed  ·  preliminary sizes",
                           "1:100  ·  1:50  ·  1:20")
    # geometry
    cad.panel(x, y + h - 300, 280, 292, "CANONICAL CELL  ·  1:100")
    draw_canonical_cell(cad, x + 140, y + h - 170)

    cad.panel(x + 288, y + h - 300, 300, 292, "TENSION NET  ·  schematic")
    # net
    cx, cy = x + 438, y + h - 150
    for i in range(6):
        a = math.radians(60 * i)
        cad.line((cx + 90 * math.cos(a), cy + 90 * math.sin(a)),
                 (cx + 90 * math.cos(a + 2.09), cy + 90 * math.sin(a + 2.09)),
                 layer="S-CABLE", rgb_=COL["INK"], lw=20)
    for pid, (wx, wy) in list(POD_POS.items())[0:12]:
        cad.circle((cx + wx / 1800, cy + wy / 1800), 3.2, layer="A-WALL", rgb_=COL["NAVY"])
    cad.mtext(x + 300, y + h - 290, "Primary Ø 85 mm Macalloy 460  ·  Secondary Ø 48 mm  ·  48 anchors  ·  sizes PRELIMINARY", h=1.8, w=270)

    cad.panel(x + 596, y + h - 300, w - 596, 292, "STRUCTURAL ELEVATION  ·  1:500")
    draw_struct_elev(cad, x + 610, y + h - 280)

    cad.panel(x, y + 210, 430, h - 520, "ROCK ANCHOR  ·  1:20 proposed")
    draw_anchor(cad, x + 30, y + 230)

    cad.panel(x + 438, y + 210, w - 438, h - 520, "CELL NODE + PORTAL  ·  1:50")
    draw_portal(cad, x + 560, y + 320)

    cad.panel(x, y + 8, w, 194, "DISASSEMBLY SEQUENCE  ·  ZERO-TRACE OBJECTIVE (not a guarantee of no residual work)")
    seq = [
        ("01", "ETFE unclamped,\ndeflated, rolled"),
        ("02", "CFRP frames\nunbolted, packed"),
        ("03", "Cables unreeled\nin reverse order"),
        ("04", "Dywidag bars out;\nholes grouted flush"),
        ("05", "Portal sealed;\nhelipad marks off"),
        ("06", "Trails fade\nin one season"),
    ]
    for i, (n, t) in enumerate(seq):
        px = x + 16 + i * 142
        cad.rect(px, y + 24, 128, 150, fill=(255, 255, 255), rgb_=COL["NAVY"], lw=18)
        cad.mtext(px + 8, y + 140, n, h=8, w=40, bold=True, rgb_=COL["NAVY"])
        cad.mtext(px + 8, y + 50, t, h=2.3, w=112)
    cad.mtext(x + 16, y + 12, "Residual: tunnel excavation, grouted holes, marine mooring points. Sealing ≠ never excavating. Ethic = reversibility of the hanging field.", h=1.8, w=840, rgb_=COL["MUTED"])


def draw_canonical_cell(cad, cx, cy):
    s = 100  # 1:100, 10 m ~ 100 mm
    # outline hex 10.8 m = 108 mm
    r = 108 / math.sqrt(3)
    cad.pline(hex_pts(cx, cy, r), layer="A-WALL", rgb_=COL["NAVY"], lw=40)
    # floors
    cad.line((cx - 50, cy - 20), (cx + 50, cy - 20), layer="A-DIM", rgb_=COL["R"], lw=18)
    cad.line((cx - 54, cy + 15), (cx + 54, cy + 15), layer="A-DIM", rgb_=COL["E"], lw=18)
    cad.line((cx - 40, cy + 48), (cx + 40, cy + 48), layer="A-DIM", rgb_=COL["H"], lw=18)
    cad.mtext(cx + 58, cy - 22, "Lv 0  MEP", h=1.8, w=40, rgb_=COL["R"])
    cad.mtext(cx + 58, cy + 13, "+3.50  deck", h=1.8, w=45, rgb_=COL["E"])
    cad.mtext(cx + 46, cy + 46, "+7.00  sleep", h=1.8, w=45, rgb_=COL["H"])
    cad.mtext(cx - 70, cy - 70, "edge 4.2 m\nhex face ~ 10.29 m\nnominal 12 m\nØ portal 3.60 m\n\nNOT 24 m tall.\nA 4.2 m-edge cell\nis ~ 10.3 m between\nopposite hex faces.", h=1.8, w=70)
    cad.scalebar(cx - 50, cy - 88, 50, 5, "1:100")


def draw_struct_elev(cad, x, y):
    cad.solid_hatch([(x, y), (x + 250, y), (x + 250, y + 40), (x, y + 40)], COL["FJORD"])
    cad.mtext(x + 6, y + 8, "FJORD +0.00", h=1.7, w=40)
    # hanging
    for i in range(5):
        px = x + 40 + i * 36
        cad.pline(hex_pts(px, y + 90, 12), layer="A-WALL", rgb_=COL["INK"], lw=18)
        cad.line((px, y + 102), (x + 200, y + 210), layer="S-CABLE", rgb_=(70, 80, 90), lw=13)
    cad.pline([(x + 180, y + 40), (x + 250, y + 40), (x + 250, y + 250), (x + 200, y + 230), (x + 180, y + 90)],
             close=True, layer="A-WALL", rgb_=(120, 125, 128), lw=18)
    cad.mtext(x + 6, y + 230, "Cliff  ·  48 plates 800×800×50  ·  Ø50 Dywidag × 4.5 m  ·  PRELIMINARY", h=1.7, w=240)


def draw_anchor(cad, x, y):
    # 1:20 — 800mm plate = 40mm
    cad.solid_hatch([(x + 20, y + 40), (x + 220, y + 40), (x + 220, y + 260), (x + 20, y + 260)], (200, 202, 204))
    cad.rect(x + 70, y + 200, 40, 8, fill=(80, 90, 100), rgb_=COL["INK"], lw=25)
    cad.rect(x + 86, y + 80, 8, 120, fill=(90, 90, 90), rgb_=COL["INK"])
    cad.mtext(x + 100, y + 204, "AISI 316L plate 800 × 800 × 50", h=2.0, w=90)
    cad.mtext(x + 100, y + 140, "Ø 50 Dywidag\n4.5 m into granite\nSika Intraplast-N grout\n\nPRELIMINARY\nrequires structural engineer", h=2.0, w=90)
    cad.mtext(x + 20, y + 20, "1:20  ·  rock face to the right is NOT a survey", h=1.7, w=160, rgb_=COL["MUTED"])


def draw_portal(cad, x, y):
    cad.truncated_oct_2d(x, y, 55)
    cad.truncated_oct_2d(x + 95, y, 55)
    cad.circle((x + 47, y), 18, layer="A-WALL", rgb_=COL["NAVY"])
    cad.mtext(x + 20, y - 8, "Ø 3.60 m", h=2.0, w=40, bold=True)
    cad.mtext(x - 40, y - 80, "Boolean union is not a floor.\nAdd threshold, walking surface\nand headroom in section.\nShared face may be inclined.", h=2.0, w=160)


def board_05(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 5, "DOMESTIC & RESEARCH INTERIORS",
                           "daily life  ·  beds, benches, light control  ·  two different rooms",
                           "1:100  ·  1:50")
    # three plans
    cad.panel(x, y + h - 292, 210, 284, "CABIN POD  ·  LV 0  ·  1:100")
    draw_pod_plan(cad, x + 105, y + h - 150, "0", "cabin")
    cad.panel(x + 218, y + h - 292, 210, 284, "CABIN POD  ·  +3.50  ·  1:100")
    draw_pod_plan(cad, x + 323, y + h - 150, "3.5", "cabin")
    cad.panel(x + 436, y + h - 292, 210, 284, "CABIN POD  ·  +7.00  ·  1:100")
    draw_pod_plan(cad, x + 541, y + h - 150, "7", "cabin")

    cad.panel(x + 654, y + h - 292, w - 654, 284, "WET LAB  ·  +3.50  ·  1:100")
    draw_pod_plan(cad, x + 754, y + h - 150, "3.5", "lab")

    cad.panel(x, y + 210, 430, h - 512, "SECTION A-A  ·  ONE CELL  ·  1:50")
    draw_pod_section(cad, x + 40, y + 230)

    cad.panel(x + 438, y + 210, w - 438, h - 512, "INHABITED SECTION  ·  WATERCOLOUR  (must match the 1:100 plans)")
    cad.image("GENDO_NORWAY_8EC8.png", (x + 448, y + 218), (400, h - 530))

    cad.panel(x, y + 8, w, 194, "FIT-TEST + LIGHT / MATERIAL")
    cad.table(x + 10, y + 185, 520, [
        ["SPACE", "LIGHT", "MATERIAL", "NOTE"],
        ["Cabin lounge +3.50", "lateral + zenith", "timber + textile", "blackout for midnight sun"],
        ["Cabin sleep +7.00", "apex ETFE + canopy", "felt / timber", "8 berths drawn — not 10"],
        ["Wet lab +3.50", "controlled north", "resin bench, CFRP", "sample in → bench → store → out"],
        ["Sanctuary C02", "one sky shaft", "dark timber, felt", "not the bedroom 'celestial'"],
        ["Assembly C01", "oculus + galleries", "timber seating", "typological exception"],
    ], row_h=6.2)
    cad.mtext(x + 550, y + 140,
              "120 people / 12 residential pods = 10 beds each was the old brief.\n"
              "This set draws 8 berths in R06. To hold 120, Habitat needs more\n"
              "sleeping cells or bunk densification. Shown honestly on the sheet.\n\n"
              "Retractable bed canopies: sleep control without killing the apex.",
              h=2.05, w=310)


def draw_pod_plan(cad, cx, cy, level, kind):
    r = PLAN_R / 100.0  # 1:100
    pts = hex_pts(cx, cy, r)
    cad.pline(pts, layer="A-WALL", rgb_=COL["NAVY"], lw=40)
    cad.circle((cx, cy), 6, layer="A-FURN", rgb_=COL["MUTED"])  # stair/lift
    cad.mtext(cx - 6, cy - 2, "V", h=2.0, w=12, rgb_=COL["MUTED"])
    if kind == "cabin" and level == "0":
        rooms = [(-28, -8, 22, 16, "AIR LOCK"), (8, -18, 26, 14, "MEP"), (-10, 18, 24, 14, "STORE")]
        for rx, ry, rw, rh, t in rooms:
            cad.rect(cx + rx, cy + ry, rw, rh, rgb_=COL["MUTED"], lw=13)
            cad.mtext(cx + rx + 1, cy + ry + 4, t, h=1.6, w=rw - 1)
    elif kind == "cabin" and level == "3.5":
        cad.rect(cx - 30, cy - 8, 22, 14, rgb_=COL["MUTED"], lw=13)
        cad.mtext(cx - 28, cy - 4, "GALLEY", h=1.6, w=20)
        cad.rect(cx + 10, cy - 6, 24, 16, rgb_=COL["MUTED"], lw=13)
        cad.mtext(cx + 12, cy, "LOUNGE", h=1.6, w=20)
        cad.rect(cx - 12, cy + 16, 18, 12, rgb_=COL["MUTED"], lw=13)
        cad.mtext(cx - 10, cy + 18, "WC", h=1.6, w=16)
    elif kind == "cabin" and level == "7":
        # 8 beds
        beds = [(-32, 8), (-32, -8), (-32, -24), (12, 8), (12, -8), (12, -24), (-10, 22), (-10, -36)]
        for bx, by in beds[:8]:
            cad.rect(cx + bx, cy + by, 18, 9, rgb_=COL["H"], fill=(250, 220, 230), lw=13)
        cad.mtext(cx - 20, cy + 40, "8 berths + apex canopy", h=1.6, w=50)
    elif kind == "lab":
        cad.rect(cx - 34, cy - 6, 28, 12, rgb_=COL["R"], fill=(220, 235, 250), lw=13)
        cad.mtext(cx - 32, cy - 2, "WET BENCH", h=1.6, w=26)
        cad.rect(cx + 8, cy - 8, 24, 18, rgb_=COL["R"], lw=13)
        cad.mtext(cx + 10, cy, "FUME /\nSTORE", h=1.6, w=22)
        cad.rect(cx - 14, cy + 16, 20, 12, rgb_=COL["R"], lw=13)
        cad.mtext(cx - 12, cy + 18, "SAMPLE IN", h=1.5, w=22)
    cad.mtext(cx - 30, cy - r - 8, f"hex ~ 10.8 m  ·  1:100  ·  {kind}  ·  {level}", h=1.6, w=80, rgb_=COL["MUTED"])


def draw_pod_section(cad, x, y):
    # 1:50 — 10.3 m = 206 mm
    sc = 1000 / 50
    def Y(m):
        return y + m * sc
    def X(m):
        return x + m * sc
    # envelope diamond/hex section
    outline = [(X(0), Y(0)), (X(2.2), Y(3.5)), (X(5.4), Y(10.3)), (X(8.6), Y(3.5)), (X(10.8), Y(0)),
               (X(8.6), Y(-0.2)), (X(5.4), Y(-0.4)), (X(2.2), Y(-0.2))]
    cad.pline([(X(0), Y(0)), (X(1.8), Y(3.43)), (X(5.4), Y(10.29)), (X(9.0), Y(3.43)), (X(10.8), Y(0))],
             close=False, layer="A-WALL", rgb_=COL["NAVY"], lw=40)
    cad.line((X(0), Y(0)), (X(10.8), Y(0)), layer="A-WALL", rgb_=COL["NAVY"], lw=40)
    for zm, lab in [(0, "+0.00  MEP / air lock"), (3.5, "+3.50  living / lab deck"), (7.0, "+7.00  sleep"), (10.29, "apex ETFE")]:
        cad.line((X(-0.4), Y(zm)), (X(11.2), Y(zm)), layer="A-DIM", rgb_=COL["MUTED"], lw=9)
        cad.mtext(X(11.4), Y(zm) - 2, lab, h=1.8, w=55)
    cad.rect(X(4.8), Y(0), 0.9 * sc, 7.0 * sc, rgb_=COL["MUTED"], lw=13)
    cad.mtext(X(0.2), Y(3.6), "portal Ø 3.60 toward neighbour", h=1.7, w=70)
    cad.mtext(X(0.2), Y(-1.2), "1:50  ·  usable headroom must be checked at the hex edge", h=1.6, w=120, rgb_=COL["MUTED"])


def board_06(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 6, "COMMONS, VOIDS & RESOURCES",
                           "how absence supports collective life  ·  proposed resource strategy",
                           "diagrams  ·  1:100")
    cad.panel(x, y + h - 430, w, 422, "FOUR VOIDS  ·  OPEN VOLUME FIRST, EQUIPMENT SECOND")
    cad.image("void_sketches.png", (x + 10, y + h - 422), (360, 408))
    # four comparable sections
    voids = [
        ("V01", "WIND / LISTENING", "Keep turbines out of the visitor path.\nOpen wind channel + protected edge."),
        ("V02", "AURORA / SOLAR", "PV on edges only — do not cover the sky.\nSummer / winter viewing deck."),
        ("V03", "LIGHT-WELL / WATER", "Well stays open. Heavy tanks in Logistics,\nnot as decoration in the void."),
        ("V04", "OCULUS / DRONE", "Offset drone ledge. People ≠ deliveries.\nCivic sky remains open."),
    ]
    for i, (vid, title, note) in enumerate(voids):
        px = x + 380 + (i % 2) * 240
        py = y + h - 210 - (i // 2) * 200
        cad.rect(px, py, 228, 188, fill=(255, 255, 255), rgb_=COL["V"], lw=20)
        cad.truncated_oct_2d(px + 50, py + 110, 32)
        cad.mtext(px + 90, py + 150, vid, h=4.5, w=120, bold=True, rgb_=COL["NAVY"])
        cad.mtext(px + 90, py + 125, title, h=2.2, w=130, bold=True)
        cad.mtext(px + 12, py + 12, note, h=1.9, w=200)

    cad.panel(x, y + 210, 430, h - 650, "RESOURCE LOOP  ·  PROPOSED (not 'solved')")
    loop = [
        "COLLECT   wind V01 · sun V02 · rain/snow V03 · seawater heat T04",
        "CONVERT   heat-pump T04 · PV/wind inverters in T08",
        "STORE     thermal + optional H2 study in Logistics — not in the void",
        "DISTRIBUTE  Level 0 loops to every pod",
        "WASTE     greywater T05 · organics to Eco · solids out by cable-car",
        "BACKUP    imported fuel/food on the supply rotation — required",
    ]
    cad.mtext(x + 12, y + h - 480, "\n\n".join(loop), h=2.2, w=400)
    cad.mtext(x + 12, y + 220, "Wind + solar symbols ≠ annual autonomy.\nRain ≠ potable sufficiency. Status: PROPOSED.", h=1.9, w=400, rgb_=COL["MUTED"])

    cad.panel(x + 438, y + 210, w - 438, h - 650, "CIVIC SECTION  ·  ASSEMBLY + SANCTUARY")
    cad.mtext(x + 450, y + h - 500,
              "C01 Assembly: stepped timber, tall volume,\n+3.50 and +7.00 become galleries.\n"
              "This is a typological exception — it cannot\nalso be three full floors.\n\n"
              "C02 Sanctuary: dark, one sky shaft, still water\nas a limited accent. Different word from the\nbedroom 'Celestial Sanctuary'.\n\n"
              "V04 beside them keeps the square from closing.",
              h=2.15, w=380)

    cad.panel(x, y + 8, w, 194, "T9  RESOURCES  ·  working register")
    cad.table(x + 10, y + 185, w - 20, [
        ["SOURCE", "CONVERSION", "STORAGE", "STATUS"],
        ["Wind at V01", "turbine (study)", "Logistics, not V01", "optional / specialist"],
        ["Midnight-sun PV at V02 edges", "inverter T08", "thermal store T04", "proposed"],
        ["Rain / snow at voids", "treatment T05", "potable tanks T08", "proposed — not proven"],
        ["Seawater +4–6 °C @ 15 m", "heat-pump T04", "low-temp loop Lv0", "proposed"],
        ["Supply ship / cable-car", "—", "T08 stores", "required backup"],
    ], row_h=6.0)


def board_07(cad: CAD, ox, oy):
    x, y, w, h = cad.frame(ox, oy, 7, "SEASONAL LIFE & THE OUTDOORS",
                           "occupation through the year  ·  zero-trace outdoor layer  ·  thresholds",
                           "1:7500  ·  diagrams")
    cad.panel(x, y + h - 360, 520, 352, "SITE & EXPERIENCE MAP  ·  1:7500")
    cad.image("site_experience_map.png", (x + 8, y + h - 352), (504, 288))
    cad.north(x + 490, y + h - 80, 11)
    cad.scalebar(x + 16, y + h - 358 + 6, 40, 300, "1:7500")

    cad.panel(x + 528, y + h - 360, w - 528, 352, "SEASONAL WHEEL")
    cad.circle((x + 680, y + h - 180), 70, layer="A-ANNO", rgb_=COL["NAVY"])
    cad.mtext(x + 655, y + h - 184, "YEAR", h=3, w=50, bold=True)
    cad.mtext(x + 540, y + h - 40,
              "SUMMER  midnight sun  ·  24 h garden  ·  blackout for sleep\n"
              "AUTUMN  storms  ·  wind-harp  ·  glass watch-room\n"
              "WINTER  aurora  ·  sauna  ·  polar night light\n"
              "SPRING  returning light  ·  trails reopen",
              h=2.15, w=320)

    cad.panel(x, y + 210, w, h - 580, "OUTDOOR LAYER  ·  SEASONAL  ·  NOTHING BUILT ON THE GROUND")
    cad.table(x + 10, y + h - 230, w - 20, [
        ["LAYER", "ACTIVITY", "START FROM", "RULE"],
        ["LAND", "dog-sled / ski-touring", "Terminal", "seasonal track — no built path"],
        ["SEA", "kayak / RIB  (Moskstraumen is OFF-SITE, Lofotodden–Mosken)", "floating pier", "no new quay"],
        ["CLIFF", "ice-climbing / via-ferrata", "Terminal / cliff study G", "removable protection only"],
        ["LEARN", "W weather · G rock · T tidal · S studio", "field points, not buildings", "observational, not construction"],
        ["WELLNESS", "sauna → rest  (fjord plunge at PIER, not from the deck)", "R02 + Base Camp", "threshold: dry, change, close"],
    ], row_h=7.2)

    cad.panel(x, y + 8, 430, 194, "WELLNESS THRESHOLD")
    cad.mtext(x + 12, y + 160,
              "A jump from the hanging deck into the fjord is not a short sequence.\n"
              "Sauna / rest / changing stay in Habitat (R02).\n"
              "Sea-plunge, if pursued, is at the pier / Base Camp and is a\n"
              "separate, assessed proposal.\n\n"
              "Draw: wet clothing dry-room, water collection, storm closure.",
              h=2.1, w=400)

    cad.panel(x + 438, y + 8, w - 438, 194, "ATMOSPHERE")
    cad.image("render 3.png", (x + 448, y + 16), (400, 176))


def add_layouts(cad: CAD):
    # remove default layouts content; create 7
    # keep Model; add TAVOLA_01..07
    for i in range(7):
        name = f"TAVOLA_{i+1:02d}"
        if name in cad.doc.layouts:
            continue
        layout = cad.doc.layouts.new(name)
        try:
            layout.page_setup(paper_size=(SHEET, SHEET), margins=(0, 0, 0, 0), units="mm")
        except Exception:
            layout.dxf.paper_width = SHEET
            layout.dxf.paper_height = SHEET
        ox, oy = sheet_origin(i)
        cx, cy = ox + SHEET / 2, oy + SHEET / 2
        try:
            layout.add_viewport(
                center=(SHEET / 2, SHEET / 2),
                size=(SHEET, SHEET),
                view_center_point=(cx, cy),
                view_height=SHEET,
            )
        except Exception as e:
            print("viewport", name, e)


def main():
    cad = CAD()
    boards = [board_01, board_02, board_03, board_04, board_05, board_06, board_07]
    for i, fn in enumerate(boards):
        ox, oy = sheet_origin(i)
        print(f"drawing tavola {i+1} at {ox},{oy}")
        fn(cad, ox, oy)
    add_layouts(cad)
    cad.doc.saveas(OUT)
    print("wrote", OUT, "bytes", os.path.getsize(OUT))


if __name__ == "__main__":
    main()
