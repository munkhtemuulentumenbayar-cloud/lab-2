"""
Make TAVOLE.dxf look like the Arctic Lens 'Cyber-Glacial' presentation sheets,
while remaining a fully editable DXF.

What it does (everything is layer-driven, so it stays easy to edit):

  1. LAYER COLOURS  -> Cyber-Glacial neon palette (true-colour RGB)
  2. LINE THICKNESS -> layered lineweight hierarchy (primary bold -> detail fine)
  3. FILLS ("water colour") -> area hatches / wall poche become a soft, visible
                       CYAN wash (ICE_CYAN at ~55% transparency)
  4. BACKGROUND     -> a real solid dark rectangle (VOID_DARK) drawn behind the
                       whole sheet on its own 'BACKGROUND' layer, so the board
                       has the dark void when viewed/plotted/exported
  5. GLOW LAYERS    -> transparent cyan/emerald underlays under the primary and
                       secondary linework to recreate the bioluminescent bloom

The embedded render (IMAGE on layer '0') is left completely untouched — you
will place the final renders yourself.

NOTE for the on-screen editor background: AutoCAD's model-space background is a
DISPLAY setting (OPTIONS -> Display -> Colors -> '2D model space' -> 'Uniform
background'), it is not stored in the drawing. Set it to RGB 10,15,26 (#0A0F1A)
to match. The BACKGROUND layer here gives the same dark void for plot/export.

Palette (from glacial.py):
    ICE_CYAN    (125, 235, 255)  #7DEBFF
    EMERALD     ( 57, 255, 176)  #39FFB0
    ICE_WHITE   (224, 249, 255)  #E0F9FF
    VOID_LIGHT  ( 22,  36,  52)  #162434
    VOID_DARK   ( 10,  15,  26)  #0A0F1A
"""
import ezdxf
from ezdxf import bbox
from ezdxf.colors import float2transparency

SRC = "TAVOLE.dxf"
DST = "TAVOLE_cyberglacial.dxf"

# --- palette -----------------------------------------------------------------
ICE_CYAN   = (125, 235, 255)
EMERALD    = (57, 255, 176)
ICE_WHITE  = (224, 249, 255)
VOID_LIGHT = (22, 36, 52)
VOID_DARK  = (10, 15, 26)

# --- layer scheme: name -> (colour, lineweight in 1/100 mm) ------------------
LAYERS = {
    "1ST":         (ICE_CYAN,   50),   # primary / cut lines     0.50 mm
    "2ND":         (EMERALD,    35),   # secondary               0.35 mm
    "3RD":         (ICE_CYAN,   25),   # main plan geometry      0.25 mm
    "4TH DETAILS": (EMERALD,    15),   # fine detail             0.15 mm
    "LAYOUT":      (ICE_CYAN,   50),   # sheet frames            0.50 mm
    "TEXTS":       (ICE_WHITE,  25),   # text / annotations      0.25 mm
    "hatch":       (ICE_CYAN,    9),   # fills / wall poche      (soft cyan wash)
}

FILL_TRANSPARENCY = 0.55   # "water colour" wash: 55% see-through

# glow underlays
GLOW = {
    "GLOW-CYAN":    dict(color=ICE_CYAN, lw=100, transparency=0.80, source="1ST"),
    "GLOW-EMERALD": dict(color=EMERALD,  lw=70,  transparency=0.80, source="2ND"),
}

GLOW_TYPES = ("LINE", "SPLINE", "LWPOLYLINE", "ARC", "CIRCLE", "POLYLINE")

ACCENT = EMERALD     # red accent entities -> emerald (keeps the highlight)


def set_layer_transparency(layer, value):
    layer.set_xdata("AcCmTransparency", [(1071, float2transparency(value))])


def main():
    doc = ezdxf.readfile(SRC)
    msp = doc.modelspace()

    # 1. layer colours + lineweights ----------------------------------------
    print("=== layers (colour + lineweight) ===")
    for name, (rgb, lw) in LAYERS.items():
        layer = doc.layers.get(name)
        if layer is None:
            print(f"  !! layer {name!r} not found")
            continue
        layer.rgb = rgb
        layer.dxf.lineweight = lw
        if name == "hatch":
            set_layer_transparency(layer, FILL_TRANSPARENCY)
        print(f"  {name!r:14s} {rgb}  lw {lw} ({lw/100:.2f} mm)"
              + ("  55% transparent wash" if name == "hatch" else ""))

    # 2. fills -> SOLID 'hatch' layer (visible cyan wash) --------------------
    print("\n=== fills (hatch -> SOLID cyan 'water colour' wash) ===")
    moved_hatch = solidified = 0
    for e in msp:
        if e.dxftype() == "HATCH" and e.dxf.layer != "TEXTS":
            if e.dxf.pattern_name != "SOLID":
                e.set_solid_fill(color=256)        # patterned -> solid fill
                solidified += 1
            e.dxf.layer = "hatch"
            if e.dxf.hasattr("true_color"):
                e.dxf.discard("true_color")
            e.dxf.color = 256                       # BYLAYER
            if e.dxf.get("lineweight", -1) >= 0:
                e.dxf.lineweight = -1
            moved_hatch += 1
    print(f"  {moved_hatch} hatch entities -> 'hatch' layer (ICE_CYAN wash)")
    print(f"  {solidified} patterned hatches converted to SOLID")

    # 3. entity overrides -> clean, layer-driven sheet ------------------------
    print("\n=== entity overrides ===")
    accent = reset_col = reset_lw = 0
    for e in msp:
        if e.dxftype() == "IMAGE":
            continue

        is_red = (
            (e.dxf.layer == "1ST" and e.dxf.hasattr("true_color"))
            or (e.dxf.layer == "4TH DETAILS" and e.dxf.get("color", 256) == 1)
        )
        if is_red:
            e.rgb = ACCENT
            e.dxf.color = 256
            accent += 1
            if e.dxf.hasattr("lineweight") and e.dxf.lineweight >= 0:
                e.dxf.lineweight = -1
            continue

        if e.dxf.hasattr("true_color"):
            e.dxf.discard("true_color")
        if e.dxf.get("color", 256) != 256:
            e.dxf.color = 256
            reset_col += 1
        if e.dxf.get("lineweight", -1) >= 0:
            e.dxf.lineweight = -1
            reset_lw += 1

    print(f"  {accent} red accents -> EMERALD")
    print(f"  {reset_col} colour overrides -> BYLAYER")
    print(f"  {reset_lw} lineweight overrides -> BYLAYER")
    print("  IMAGE (render) untouched on layer '0'")

    # 4. glow underlays ------------------------------------------------------
    print("\n=== glow layers ===")
    for name, spec in GLOW.items():
        layer = doc.layers.add(name, color=7)
        layer.rgb = spec["color"]
        layer.dxf.lineweight = spec["lw"]
        layer.dxf.linetype = "Continuous"
        set_layer_transparency(layer, spec["transparency"])

        copies = []
        for e in msp:
            if e.dxf.layer == spec["source"] and e.dxftype() in GLOW_TYPES:
                c = e.copy()
                # strip extension dictionaries & reactors from the copy so it is
                # a clean plain entity (avoids dangling plugin-proxy refs)
                if c.has_extension_dict:
                    c.discard_extension_dict()
                c.dxf.layer = name
                if c.dxf.hasattr("true_color"):
                    c.dxf.discard("true_color")
                c.dxf.color = 256
                c.dxf.lineweight = -1
                copies.append(c)
        for c in copies:
            msp.add_entity(c)
        print(f"  {name!r:14s} {spec['color']}  lw {spec['lw']} "
              f"({spec['lw']/100:.2f} mm)  {spec['transparency']:.0%} transparent  "
              f"<- {len(copies)} entities from {spec['source']!r}")

    # 5. background rectangle (dark void behind the whole board) ------------
    print("\n=== background layer ===")
    bg_layer = doc.layers.add("BACKGROUND", color=7)
    bg_layer.rgb = VOID_DARK
    bg_layer.dxf.lineweight = -3
    bg_layer.dxf.linetype = "Continuous"

    # cover everything except the placeholder render image
    entities = [e for e in msp if e.dxftype() != "IMAGE"]
    ext = bbox.extents(entities)
    pad = 150.0
    x1 = ext.extmin.x - pad
    y1 = ext.extmin.y - pad
    x2 = ext.extmax.x + pad
    y2 = ext.extmax.y + pad

    backdrop = msp.add_hatch()
    backdrop.dxf.layer = "BACKGROUND"
    backdrop.dxf.color = 256
    backdrop.set_solid_fill()
    backdrop.paths.add_polyline_path(
        [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], is_closed=True
    )
    print(f"  BACKGROUND rectangle ({x1:.0f},{y1:.0f}) -> ({x2:.0f},{y2:.0f}) "
          f"VOID_DARK {VOID_DARK}")

    # physically order the modelspace: backdrop -> fills -> glow -> linework
    # (this also fixes the database order so previews/plots match the draw order)
    order = list(msp)                       # everything incl. backdrop (last)
    grouped = (
        [backdrop]
        + [e for e in order if e is not backdrop and e.dxf.layer == "hatch"]
        + [e for e in order if e.dxf.layer.startswith("GLOW")]
        + [e for e in order
           if e is not backdrop
           and e.dxf.layer != "hatch"
           and not e.dxf.layer.startswith("GLOW")]
    )
    for e in order:
        msp.unlink_entity(e)
    for e in grouped:
        msp.add_entity(e)

    # explicit draw order: backdrop -> fills -> glow -> linework
    # (smallest sort handle = drawn first = behind)
    redraw = {backdrop.dxf.handle: "00000001"}
    n = 2
    for e in grouped:
        if e is backdrop:
            continue
        redraw[e.dxf.handle] = f"{n:08X}"
        n += 1
    msp.set_redraw_order(redraw)

    doc.saveas(DST)
    print(f"\nsaved {DST}")


if __name__ == "__main__":
    main()
