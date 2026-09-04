"""
Make TAVOLE.dxf look like the Arctic Lens 'Cyber-Glacial' presentation sheets,
while remaining a fully editable DXF.

What it does (everything is layer-driven, so it stays easy to edit):

  1. LAYER COLOURS  -> Cyber-Glacial neon palette (true-colour RGB)
  2. LINE THICKNESS -> layered lineweight hierarchy (primary bold -> detail fine)
  3. BACKGROUND     -> solid void (#0A0F1A) for model & paper space viewports
  4. FILLS          -> wall poche / area hatches moved to a muted 'hatch' layer
                       (subtle VOID_LIGHT instead of bright neon fills)
  5. GLOW LAYERS    -> transparent cyan/emerald underlays under the primary and
                       secondary linework to recreate the bioluminescent bloom
                       (freeze or delete GLOW-* if you prefer clean lines)

The embedded render (IMAGE on layer '0') is left completely untouched —
you will place the final renders yourself.

Palette (from glacial.py):
    ICE_CYAN    (125, 235, 255)  #7DEBFF
    EMERALD     ( 57, 255, 176)  #39FFB0
    ICE_WHITE   (224, 249, 255)  #E0F9FF
    VOID_LIGHT  ( 22,  36,  52)  #162434
    VOID_DARK   ( 10,  15,  26)  #0A0F1A
"""
import ezdxf
from ezdxf.lldxf.types import DXFTag
from ezdxf.lldxf.extendedtags import ExtendedTags
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
    "hatch":       (VOID_LIGHT,  9),   # fills / wall poche      0.09 mm
}

# glow underlays
GLOW = {
    "GLOW-CYAN":    dict(color=ICE_CYAN, lw=100, transparency=0.80, source="1ST"),
    "GLOW-EMERALD": dict(color=EMERALD,  lw=70,  transparency=0.80, source="2ND"),
}

GLOW_TYPES = ("LINE", "SPLINE", "LWPOLYLINE", "ARC", "CIRCLE", "POLYLINE")

ACCENT = EMERALD     # red accent entities -> emerald (keeps the highlight)
VOID_DARK_INT = (VOID_DARK[0] << 16) | (VOID_DARK[1] << 8) | VOID_DARK[2]


def add_background(doc, owner_handle, rgb_int):
    """Solid BACKGROUND object (viewport colour) owned by a block record."""
    obj = doc.objects.add_dxf_object_with_reactor("BACKGROUND", {"owner": owner_handle})
    handle = obj.dxf.handle
    obj.store_tags(ExtendedTags([
        DXFTag(0, "BACKGROUND"),
        DXFTag(5, handle),
        DXFTag(330, owner_handle),
        DXFTag(100, "AcDbBackground"),
        DXFTag(90, 0),             # solid
        DXFTag(63, rgb_int),       # model-space colour
        DXFTag(73, rgb_int),       # paper-space colour
        DXFTag(83, rgb_int),
    ]))
    return obj


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
        print(f"  {name!r:14s} {rgb}  lw {lw} ({lw/100:.2f} mm)")

    # 2. background colour ---------------------------------------------------
    print("\n=== background ===")
    for br in doc.block_records:
        if br.dxf.name.startswith("*Model_Space") or br.dxf.name.startswith("*Paper_Space"):
            add_background(doc, br.dxf.handle, VOID_DARK_INT)
            print(f"  {br.dxf.name!r} -> #{VOID_DARK[0]:02X}{VOID_DARK[1]:02X}{VOID_DARK[2]:02X}")

    # 3. fills -> muted 'hatch' layer ---------------------------------------
    print("\n=== fills (hatch) ===")
    moved_hatch = 0
    for e in msp:
        if e.dxftype() == "HATCH" and e.dxf.layer != "TEXTS":
            e.dxf.layer = "hatch"
            if e.dxf.hasattr("true_color"):
                e.dxf.discard("true_color")
            e.dxf.color = 256                       # BYLAYER
            if e.dxf.get("lineweight", -1) >= 0:
                e.dxf.lineweight = -1
            moved_hatch += 1
    print(f"  {moved_hatch} hatch entities -> 'hatch' layer (muted VOID_LIGHT)")

    # 4. entity overrides -> clean, layer-driven sheet ------------------------
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

    # 5. glow underlays ------------------------------------------------------
    print("\n=== glow layers ===")
    for name, spec in GLOW.items():
        layer = doc.layers.add(name, color=7)
        layer.rgb = spec["color"]
        layer.dxf.lineweight = spec["lw"]
        layer.dxf.linetype = "Continuous"
        layer.set_xdata("AcCmTransparency",
                        [(1071, float2transparency(spec["transparency"]))])

        copies = []
        for e in msp:
            if e.dxf.layer == spec["source"] and e.dxftype() in GLOW_TYPES:
                c = e.copy()
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

    doc.saveas(DST)
    print(f"\nsaved {DST}")


if __name__ == "__main__":
    main()
