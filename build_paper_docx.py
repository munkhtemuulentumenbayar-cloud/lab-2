#!/usr/bin/env python3
"""Build 'The Arctic Lens — Combined Paper (EN).docx' from the revised text."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# base style
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

def title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(20)
    return p

def meta(label, value):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    if label:
        r = p.add_run(label + " ")
        r.bold = True
    p.add_run(value)
    return p

def h1(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(14)
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    return p

def h2(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    return p

def para(segments, style=None):
    """segments: list of (text, bold, italic) tuples."""
    p = doc.add_paragraph(style=style)
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
    return p

def bullet(segments):
    p = doc.add_paragraph(style="List Bullet")
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
    return p

def numbered(segments):
    p = doc.add_paragraph(style="List Number")
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
    return p

# ---------------------------------------------------------------- title block
title("THE ARCTIC LENS: SPATIAL SUSPENSION AND THE ZERO-TRACE ETHIC")
meta("Master's Degree Thesis in Architecture — Università degli Studi di Udine (DPIA)", "")
meta("Author:", "Munkhtemuulen Tumenbayar")
meta("Site:", "Lofoten Archipelago, Moskenesøya — Bunesfjorden (68.22°N, 13.56°E)")

# ------------------------------------------------------------------- abstract
h1("ARCHITECTURAL ABSTRACT")
para([("There exists a category of space that resists and refutes architecture—not because the place is inhospitable to life, but because it is already, in itself, complete and perfectly made. The Lofoten Archipelago, stretching between 67° and 68.5° North along the north-western edge of the Norwegian continental shelf, belongs precisely to this category. Its granite ravines rise sheer and monumental straight out of the sea. To build in Lofoten, therefore, is not a matter of resolving questions of spatial enclosure and walls. It is to enter into a dialogue with powerful geological, atmospheric, optical, and temporal forces that existed two billion years before the first human civilization and will remain for two billion years after.", False, False)])
para([("The Arctic Lens", True, False),
      (" is an architecture that earns its right to exist in this landscape by adhering to the principle of never once touching the ground. It is a spatial aerial node with a ", False, False),
      ("zero-ground-footprint", True, False),
      ("—a horizontal matrix of 32 Truncated Octahedral pods suspended in the atmospheric threshold above the Lofoten fjords, at the fixed geodetic coordinates of 68.22°N, 13.56°E. This cloud-like settlement rests on no lower supporting column. It is suspended 22 m in the air above the fjord by a multi-point cable network of Ø85 mm high-tensile, locked-coil steel cables anchored into the vertical face of ancient Precambrian granite.", False, False)])
para([("The 32 polyhedral cells form a continuous matrix extended along the horizontal axis. The spatial program is divided into five functional categories:", False, False)])
numbered([("8 Marine Biology & Climate Research Laboratories", True, False)])
numbered([("12 Residential Pods", True, False)])
numbered([("6 Shared Eco-Terraces", True, False)])
numbered([("2 Technical Cores", True, False)])
numbered([("4 Aerodynamic Voids", True, False)])
para([("The 120 inhabitants arrive via two zero-trace routes: by land through a concealed mountain terminal linked to the E10 highway, or by sea via a semi-submersible floating ocean dock that protects the underlying ", False, False),
      ("Lophelia pertusa", False, True),
      (" cold-water coral reefs. From these logistical nodes, inhabitants ascend through a 45-metre Vertical Glass Core fixed to the rock face before crossing horizontal, tensile transit bridges of carbon fiber and transparent ETFE membrane into a continuous, doorless interior.", False, False)])

# ------------------------------------------------------------------ chapter I
h1("CHAPTER I: THE TECTONICS OF THE WEB — SARACENO'S SPATIAL PHILOSOPHY")
h2("1.1 From Art Installation to Lived Reality")
para([("The spatial lineage of The Arctic Lens derives directly from Tomás Saraceno's ", False, False),
      ("Cloud Cities", False, True),
      (" and ", False, False),
      ("Arachnophilia", False, True),
      (" research, scaling the logic of suspended polyhedral artwork into a permanent, thermally conditioned architecture.", False, False)])
para([("The Truncated Octahedron was chosen based on Lord Kelvin's 1887 principle: it is the single geometric solid capable of packing three-dimensional space without gaps while holding the surface-area-to-volume ratio to an absolute minimum. Each pod, with an internal volume of 837.8 m³, is clad with only 282.6 m² of surface—a 34.2% material savings compared to an equivalent sphere.", False, False)])
para([("The 32 pods connect directly to one another through their hexagonal faces via Ø3,600 mm CFRP-reinforced ", False, False),
      ("Boolean Union portals", True, False),
      (". These portals are topological continuities through which the interior of one pod flows seamlessly into the next, forming a continuous living field without corridors or dividing doors.", False, False)])
h2("1.2 The Atmospheric Envelope: Material Stratification")
para([("The outer skin weighs less than 4 kg/m² (850 kg per pod vs. 12 tonnes for a conventional glass façade) and operates across four metabolic layers:", False, False)])
numbered([("Outer Layer:", True, False), (" 200 µm ETFE fluoropolymer film printed with a gradient ceramic frit pattern to diffuse harsh Midnight Sun glare.", False, False)])
numbered([("Thermal Cavity:", True, False), (" 200 mm sealed argon-gas cavity held at +200 to +300 Pa positive pressure, providing a thermal performance of U = 0.8–1.1 W/m²K.", False, False)])
numbered([("Structural Skeleton:", True, False), (" CFRP ring-frame made of Toray T700S carbon fiber (12.5 mm wall thickness, DN150 tube) providing structural rigidity with zero risk of marine corrosion.", False, False)])
numbered([("Inner Layer:", True, False), (" 150 µm ETFE film embedded with a 50 mm-spaced NiCr radiant heating grid, warming the surface to 30°C to eliminate internal icing and fogging.", False, False)])

# ----------------------------------------------------------------- chapter II
h1("CHAPTER II: SPATIAL LOGIC OF THE CONTEXT — THE LOFOTEN PARADIGM")
h2("2.1 Lightness as an Ethical Necessity")
para([("Against the extreme climate of Lofoten (42 m/s winds, -20°C winter temperatures), erecting a heavy concrete monument would incur an unpaid ecological debt to the ancient granite.", False, False)])
para([("The Arctic Lens responds with extreme lightness. The 108-tonne total structural mass is distributed evenly across 48 rock anchor points. The suspended matrix acts as a single pendulum system with a natural oscillation period of 8.5 seconds, allowing the building to sway gently with storms rather than fighting wind loads.", False, False)])
h2("2.2 Territorial Infrastructure and Access Logistics")
bullet([("Land Access (Territorial Master Plan — Scale 1:1500):", True, False), (" A spur from highway E10 enters a granite tunnel leading to a subsurface smart logistics terminal carved 15 m inside the mountain, completely invisible from the exterior landscape.", False, False)])
bullet([("Marine Access:", True, False), (" Research vessels berth at a floating ocean dock set 200 m from the cliff. Moored 5 m below the surface, the dock exerts no compressive pressure on the seabed, fully protecting the ", False, False), ("Lophelia pertusa", False, True), (" coral reefs at 80–200 m depths in accordance with the Norwegian Nature Diversity Act (", False, False), ("Naturmangfoldloven", False, True), (").", False, False)])

# ---------------------------------------------------------------- chapter III
h1("CHAPTER III: THE TRANSIT MATRIX")
h2("3.1 The Vertical Glass Core")
para([("Inhabitants ascend from the mountain terminal to the suspended cluster via a 45-metre Vertical Glass Core. Built with S460 steel SHS 400 × 400 × 20 mm spine columns and quadruple-laminated low-iron glass, the core is pinned laterally to the cliff face using Ø40 mm Dywidag tie-backs at 5 m intervals.", False, False)])
h2("3.2 Suspended Tensile Transit Bridges")
para([("Horizontal bridges spanning 18 to 42 m connect the glass core to the pod matrix. Formed by Ø85 mm Macalloy cables, Ø2,400 mm CFRP ring frames, and transparent ETFE membranes, the bridges feature laminated transparent glass walkways suspended over the open fjord.", False, False)])

# ----------------------------------------------------------------- chapter IV
h1("CHAPTER IV: MORPHOLOGICAL EVOLUTION & SECTIONAL STRATIFICATION")
h2("4.1 Pod Sectional Stratification (Tavola 3 — Section A-A', Scale 1:80)")
para([("To align with the master drawing panels, the vertical domain of the cluster and its primary pod sections are stratified across four primary elevation datums:", False, False)])
bullet([("Level +0.00 m (Life-Support & Technical Base):", True, False), (" Encloses high-pressure environmental airlocks, storage, greywater recycling loops, power distribution, and seawater heat-pump units drawing +4°C to +6°C thermal energy from a sea depth of 15 m.", False, False)])
bullet([("Level +8.00 m (Research & Active Bio-Commons):", True, False), (" Houses climate-controlled hydro-gardens/aquaponics, active scientific workstations, wet labs, and micro-vegetation terraces (150 mm clay aggregate soil growing dwarf polar willow and mosses).", False, False)])
bullet([("Level +16.00 m (Equatorial Social Core & Living Quarters):", True, False), (" Dedicated to crew accommodation pods, communal dining lounges, quiet study spaces, and archival library habitats connected face-to-face via the Ø3,600 mm open portals.", False, False)])
bullet([("Level +24.00 m (Celestial Sanctuary & Upper Apex Lens):", True, False), (" The uppermost residential refuge under the polyhedral dome, capped by a 100% unfritted, crystal-clear 7.3 m ETFE zenith lens. It operates as a living sundial during the summer Midnight Sun and an unobstructed viewing dome for the Aurora Borealis in winter.", False, False)])
h2("4.2 Structural Anchoring & Cable Network (Tavola 2 — Scale 1:750)")
bullet([("Primary Cables:", True, False), (" Ø85 mm Macalloy 460 locked-coil cables.", False, False)])
bullet([("Secondary Cables:", True, False), (" Ø48 mm horizontal inter-pod connections (1,200 m total cable length).", False, False)])
bullet([("Rock Anchor Plates:", True, False), (" 48 AISI 316L stainless steel plates (800 × 800 × 50 mm) fixed via Ø50 mm Dywidag tie-backs drilled 4.5 m into bedrock and grouted with Sika Intraplast-N expansive mortar.", False, False)])

# ------------------------------------------------------------------ chapter V
h1("CHAPTER V: THE SPATIAL LOGIC OF THE FOUR AERODYNAMIC VOIDS")
para([("Four of the 32 pods are deliberately left unclad—stripped of ETFE membranes and floors, leaving only the bare CFRP structural frame open to the sky.", False, False)])
numbered([("Aerodynamic Load Relief:", True, False), (" By allowing 42 m/s winds to pass directly through the cluster, the wind resistance coefficient drops from 1.1 to 0.68, reducing total lateral dynamic wind forces by 38.2% (from 2,666 kN down to 1,648 kN).", False, False)])
numbered([("Luminous Wells:", True, False), (" They channel raw, unfiltered zenith light deep into the inner cluster, casting sharp chiaroscuro shadows across adjacent pod walls.", False, False)])
numbered([("Acoustic Wind Harps:", True, False), (" Internal Ø18 mm CFRP cables are tuned to generate vortex-induced vibrations under high winds, producing sub-bass frequencies (28 to 65 Hz) that translate Arctic storms into deep interior resonance.", False, False)])

# ----------------------------------------------------------------- chapter VI
h1("CHAPTER VI: CONCLUSION AND ARCHITECTURAL MANIFESTO")
h2("6.1 The Synthesis of Reversibility")
para([("True civilizational maturity is measured not by the weight of the monuments a society raises, but by the precision of its departures.", False, True)])
para([("When the 100-year service lifespan of The Arctic Lens concludes:", False, False)])
numbered([("ETFE membranes are unclamped, deflated, and rolled.", False, False)])
numbered([("CFRP frames are unbolted and flat-packed onto the floating dock.", False, False)])
numbered([("Macalloy cables are unreeled in a controlled engineering sequence.", False, False)])
numbered([("Dywidag anchor bars are extracted, and the 48 anchor holes (75 mm diameter) are backfilled with grout flush with the rock surface.", False, False)])
para([("Within ten years, native lichen and moss will cover the plugged holes, rendering them indistinguishable from the surrounding Precambrian granite. The fjord will remember nothing.", False, False)])

# ------------------------------------------------------------- summary table
h1("SUMMARY OF ESSENTIAL TECHNICAL DATA")
rows = [
    ("Site Location", "68.22°N, 13.56°E — Lofoten, Norway", "Tavola 1 (Masterplan)"),
    ("Primary Drawing Scales", "1:1500 (Masterplan), 1:750 (Anchoring), 1:80 (Section)", "Tavola 1, 2, 3 Title Blocks"),
    ("Suspension Elevation", "+22.00 m above fjord water line", "Tavola 2 (Structural Elevation)"),
    ("Pod Elevation Datums", "+0.00 m / +8.00 m / +16.00 m / +24.00 m", "Tavola 2 & 3 Datums"),
    ("Cluster Pod Count", "32 Truncated Octahedra (8 Labs, 12 Housing, 6 Terraces, 2 Tech, 4 Voids)", "Tavola 2 (Cluster Zoning)"),
    ("Pod Dimensions", "Ø10.8 m internal (12 m geometric), 4.2 m edge length", "Tavola 2 & 3 Geometries"),
    ("Volume / Surface Area", "837.8 m³ volume / 282.6 m² surface area (34.2% savings vs sphere)", "Tavola 2 Text Block"),
    ("Primary Cable System", "Ø85 mm Macalloy 460 locked-coil cables", "Tavola 2 Cable Detail"),
    ("Rock Anchors", "48 AISI 316L plates (800 × 800 × 50 mm), Ø50 mm Dywidag bars", "Tavola 2 Anchor Detail"),
    ("Envelope Weight & U-Value", "<4 kg/m² (850 kg/pod), U = 0.8–1.1 W/m²K", "Tavola 3 Envelope Callouts"),
    ("Wind Load Reduction", "Porous voids reduce lateral load by 38.2% (2,666 kN to 1,648 kN)", "Tavola 1 & 2 Void Diagrams"),
]
table = doc.add_table(rows=1, cols=3)
table.style = "Light Grid Accent 1"
table.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = table.rows[0].cells
for i, htext in enumerate(("Parameter", "Value / Metric", "Drawing Alignment")):
    hdr[i].text = ""
    r = hdr[i].paragraphs[0].add_run(htext)
    r.bold = True
for a, b, c in rows:
    cells = table.add_row().cells
    for i, val in enumerate((a, b, c)):
        cells[i].text = ""
        r = cells[i].paragraphs[0].add_run(val)
        if i == 0:
            r.bold = True

out = "The Arctic Lens — Combined Paper (EN).docx"
doc.save(out)
print(f"wrote {out}")
