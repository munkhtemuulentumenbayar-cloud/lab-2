"""
Edit TAVOLE.dxf: change LAYER COLOURS + LINE THICKNESS (lineweight) to the
Arctic Lens 'Cyber-Glacial' style.

The embedded render (IMAGE on layer '0') is left completely untouched.

Colour palette (from glacial.py):
    ICE_CYAN    (125, 235, 255)  #7DEBFF   primary
    EMERALD     ( 57, 255, 176)  #39FFB0   secondary / detail
    ICE_WHITE   (224, 249, 255)  #E0F9FF   text / annotations
    VOID_LIGHT  ( 22,  36,  52)  #162434   hatch fills
    VOID_DARK   ( 10,  15,  26)  #0A0F1A   background

Lineweight hierarchy (lineweight unit = 1/100 mm):
    50 -> 0.50 mm  bold primary / sheet frame
    35 -> 0.35 mm  secondary
    25 -> 0.25 mm  main body + text
    15 -> 0.15 mm  fine detail
     9 -> 0.09 mm  hatch fills
"""
import ezdxf

SRC = "TAVOLE.dxf"
DST = "TAVOLE_cyberglacial.dxf"

# layer -> (RGB colour, lineweight in 1/100 mm)
LAYERS = {
    # name:             colour                lw    meaning
    "1ST":         ((125, 235, 255), 50),   # ICE_CYAN   primary lines
    "2ND":         (( 57, 255, 176), 35),   # EMERALD    secondary lines
    "3RD":         ((125, 235, 255), 25),   # ICE_CYAN   main structure
    "4TH DETAILS": (( 57, 255, 176), 15),   # EMERALD    fine detail
    "LAYOUT":      ((125, 235, 255), 50),   # ICE_CYAN   sheet frame
    "TEXTS":       ((224, 249, 255), 25),   # ICE_WHITE  text / annotations
    "hatch":       (( 22,  36,  52),  9),   # VOID_LIGHT hatch fills
}
ACCENT = (57, 255, 176)   # EMERALD — for the explicit red accent entities


def main():
    doc = ezdxf.readfile(SRC)
    msp = doc.modelspace()

    print("=== layer colour + lineweight ===")
    for name, (rgb, lw) in LAYERS.items():
        layer = doc.layers.get(name)
        if layer is None:
            print(f"  !! layer {name!r} not found")
            continue
        old_c = layer.dxf.get("true_color") or f"ACI {layer.dxf.color}"
        old_lw = layer.dxf.lineweight
        layer.rgb = rgb
        layer.dxf.lineweight = lw
        print(f"  {name!r:14s} colour {rgb} (was {old_c})   lw {lw} = {lw/100:.2f} mm (was {old_lw})")

    print("\n=== entity-level overrides ===")
    accent = 0
    reset_lw = 0
    reset_col = 0
    for e in msp:
        if e.dxftype() == "IMAGE":
            continue  # leave the render alone

        # red accent entities -> emerald (keeps the highlight intent,
        # matching the repo's hue_shift_red_to_accent)
        is_red = (
            (e.dxf.layer == "1ST" and e.dxf.hasattr("true_color"))
            or (e.dxf.layer == "4TH DETAILS" and e.dxf.get("color", 256) == 1)
        )
        if is_red:
            e.rgb = ACCENT          # true colour = emerald
            e.dxf.color = 256       # BYLAYER fallback
            accent += 1
            if e.dxf.hasattr("lineweight") and e.dxf.lineweight >= 0:
                e.dxf.lineweight = -1
            continue

        # everything else -> BYLAYER colour (layer-driven sheet)
        if e.dxf.hasattr("true_color"):
            e.dxf.discard("true_color")
        if e.dxf.get("color", 256) != 256:
            e.dxf.color = 256
            reset_col += 1

        # every explicit lineweight override -> BYLAYER
        if e.dxf.get("lineweight", -1) >= 0:
            e.dxf.lineweight = -1   # BYLAYER
            reset_lw += 1

    print(f"  {accent} red accent entities -> EMERALD")
    print(f"  {reset_col} entity colour overrides reset to BYLAYER")
    print(f"  {reset_lw} entity lineweight overrides reset to BYLAYER")
    print("  IMAGE (render) left untouched on layer '0'")

    doc.saveas(DST)
    print(f"\nsaved {DST}")


if __name__ == "__main__":
    main()
