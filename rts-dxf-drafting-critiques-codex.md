# Rocket Tool Sketcher DXF Drafting Critiques and Codex-Oriented Remediation Plan

## Purpose

This document consolidates the drafting-specialist critique of the generated Rocket Tool Sketcher DXF output and the deeper technical critique of the actual DXF file `tooling-set-annotated.dxf`.

It is written for a coding agent or CAD-export implementation agent that needs to improve the DXF output so it can progress from a geometry/debug drawing toward a machinist-ready production drawing.

This is **not** a UI design task. This is **not** a broad architecture task. The focus is the generated 2D DXF production drawing output for an axisymmetric rocket tooling set.

The current generated drawing should be treated as a useful geometry validation export, but **not yet a machinist-ready drawing**.

---

# 1. Executive Summary

The generated Rocket Tool Sketcher DXF correctly captures much of the underlying BP Core Burner geometry. The rammer count, progressive rammer lengths, bore depths, and bore diameters appear coherent. The drawing also appears to correctly place the first/longest A-rammer backside nozzle taper at the working end, with the taper ending at the bore opening.

However, the current DXF is **not acceptable as a production shop drawing** without revisions.

The largest problems are:

1. The **spindle is upside down** relative to the expected/legacy presentation and should be flipped or explicitly labeled.
2. The spindle taper angle is shown as approximately **178.75° / 179°**, which is a drafting artifact. It should be shown as the actual manufacturing taper, such as `1.25° per side` for BP Core Burner.
3. The A-rammer taper angle is encoded as **225°**, which is also a drafting artifact. It should be shown as the intended `45° backside nozzle taper`.
4. The DXF dimension style appears to use a **100× linear dimension scale factor**. This risks displaying dimensions such as `75` instead of `0.750` and `806.25` instead of `8.0625`. This is a critical issue.
5. The file lacks basic machinist drawing information: title block, units note, material, tolerances, finish, revision, scale, edge-break notes, bore notes, and concentricity requirements.
6. The drawing does not clearly distinguish visible external geometry, hidden internal bores, centerlines, do-not-pass marks, and construction/debug geometry.
7. Diameter symbols are missing or inconsistent.
8. The repeated rammer head/do-not-pass line is currently ambiguous and appears as a one-sided notch/jog in the profile. It should be explicitly defined as a scribed/engraved mark, a machined groove with dimensions, or reference-only geometry.
9. Some part titles and dimensions are too small, cramped, or clipped.
10. The current combined-sheet layout is useful for debugging but weak for production.

The correct direction is to split output intent into at least two modes:

```text
1. Debug / legacy comparison drawing
2. Machinist production drawing
```

The current file belongs closer to mode 1. A machinist-ready output needs stricter drafting conventions, corrected dimensions, proper callouts, and production notes.

---

# 2. Known Drawing Context

The reviewed drawing appears to represent a **BP Core Burner** toolset for:

```text
A = 0.750 in
```

Expected BP Core Burner parameters:

```text
A = 0.750
B = 10*A = 7.500
C = 7.5*A = 5.625
D = 0.5*A = 0.375
E = 1.25 deg
F = 0.75*A = 0.5625
G = 30 deg
H = 4
I = 45 deg
ri = 1.5*A = 1.125
```

Expected parts:

```text
1. Spindle / core former
2. Solid rammer
3. Full-depth A rammer
4. Progressive rammer 1
5. Progressive rammer 2
```

Expected rammer lengths:

```text
solid rammer:
B - (C + F) + ri
= 7.500 - 6.1875 + 1.125
= 2.4375 -> 2.438 rounded

full-depth A rammer:
B - F + ri
= 7.500 - 0.5625 + 1.125
= 8.0625 -> 8.063 rounded

progressive rammer 1:
B - F - C/3 + ri
= 7.500 - 0.5625 - 1.875 + 1.125
= 6.1875 -> 6.188 rounded

progressive rammer 2:
B - F - 2C/3 + ri
= 7.500 - 0.5625 - 3.750 + 1.125
= 4.3125 -> 4.313 rounded
```

Expected rammer bore depths:

```text
full-depth A rammer: 5.625
progressive rammer 1: 3.750
progressive rammer 2: 1.875
```

Expected rammer bore diameters:

```text
full-depth A rammer: 0.375
progressive rammer 1: about 0.293
progressive rammer 2: about 0.211
```

The generated drawing appears broadly consistent with these values.

---

# 3. File-Level Technical Findings

The actual DXF structure appears to have these file-level characteristics:

| Item | Finding |
|---|---|
| DXF version | AutoCAD 2010 / `AC1024` |
| Generator | likely `ezdxf` |
| Model units | `$INSUNITS = 1`, meaning inches |
| Measurement flag | `$MEASUREMENT = 1`, metric defaults |
| Geometry entities | closed `LWPOLYLINE` profiles |
| Centerlines | `LINE` entities on `CENTER` layer |
| Hidden/internal geometry | `LINE` entities on `HIDDEN` layer |
| Dimensions | `DIMENSION` entities |
| Titles | `TEXT` entities |
| Blocks | anonymous dimension blocks only |
| Paper space/title block | not present |
| Header extents | not updated; placeholder extreme values remain |

The file has a useful start toward layer separation:

```text
PROFILE
HIDDEN
CENTER
DIM
TEXT
TITLE
```

This is acceptable for a debug drawing, but insufficient for a machinist-ready drawing.

---

# 4. Critical Issue: Dimension Scaling Appears Wrong

## Problem

The DXF appears to have:

```text
$DIMLFAC = 100.0
$DIMDEC = 2
$DIMZIN = 12
```

The geometry itself is in inches, but the dimension style applies a **100× linear dimension scale factor**.

That can cause CAD systems to display dimensions like:

```text
75
618.75
562.5
37.5
12.95
112.5
806.25
29.32
21.13
```

when the intended inch dimensions are:

```text
0.750
6.1875
5.625
0.375
0.1295
1.125
8.0625
0.2932
0.2113
```

This is a **shop-stopping problem**.

A machinist could interpret these as hundredths, millimeters, scaled inches, or simply wrong dimensions.

## Required correction

Production DXF dimensions must use actual model units directly.

Use:

```text
$DIMLFAC = 1.0
```

Then format dimensions as real inch values:

```text
Ø0.750
6.188
5.625
Ø0.375
Ø0.129
1.125
8.063
Ø0.293
Ø0.211
```

If a legacy Flash-like display format is desired, implement it as dimension text formatting, not as a geometry-scale multiplier.

## Acceptance criteria

Open the DXF in at least two CAD viewers and confirm that:

```text
A dimension across a 0.750 inch rammer reads 0.750, not 75.
The full-depth A rammer length reads about 8.063, not 806.25.
The spindle length reads 5.625, not 562.5.
```

---

# 5. Critical Issue: Angle Callouts Are Wrong or Misleading

## 5.1 Spindle taper angle

The spindle taper is currently shown as approximately:

```text
178.75° or 179°
```

That is not a useful machining angle.

For BP Core Burner, the intended value is:

```text
E = 1.25°
```

The current near-180° label is likely a reflex or obtuse angle artifact from dimensioning the wrong two vectors.

## Required correction

Replace the current spindle taper angle dimension with one of the following production callouts:

```text
SPINDLE TAPER: 1.25° PER SIDE
```

or:

```text
INCLUDED SPINDLE TAPER: 2.50°
```

Best production practice is to include both angle and endpoint dimensions:

```text
Ø0.375 AT ROOT
Ø0.129 AT TIP
SPINDLE LENGTH 5.625
SPINDLE TAPER 1.25° PER SIDE
```

## 5.2 A-rammer backside nozzle taper angle

The DXF encodes the full-depth A-rammer taper angle as:

```text
225°
```

That is not acceptable as a manufacturing callout.

For BP Core Burner, the intended value is:

```text
I = 45°
```

The drawing should call it out as:

```text
45° BACKSIDE NOZZLE TAPER
```

Because this taper has a specific tooling meaning, the callout should be explicit:

```text
45° BACKSIDE NOZZLE TAPER FROM WORKING FACE TO Ø0.375 BORE OPENING.
NO FLAT LAND AT BORE OPENING.
```

If the angle convention is from the centerline instead of the working face, the note must say that. Do not let the CAD dimension engine choose a reflex angle.

## 5.3 Collar taper angle

The collar taper is shown as:

```text
30°
```

That is numerically plausible, but the drawing does not clearly state the reference convention.

Recommended callout:

```text
30° COLLAR TAPER FROM SHOULDER FACE
```

or use explicit endpoint dimensions instead of relying only on the angle.

---

# 6. Critical Issue: Spindle Is Upside Down

The spindle is currently drawn vertically with the collar at the top and the long tapered spindle extending downward. The user explicitly confirmed that the spindle is upside down.

This is a serious drafting clarity issue.

Even if the geometry is mathematically valid, the drawing should reflect either:

```text
1. working orientation
```

or:

```text
2. the legacy Rocket Tool Sketcher orientation
```

At minimum, the orientation must be labeled.

## Recommended correction

Either flip the spindle or add an explicit label:

```text
SPINDLE / CORE FORMER — SHOWN WORKING END DOWN
```

or:

```text
SPINDLE / CORE FORMER — SHOWN COLLAR END UP
```

Preferred correction: flip the spindle so the tool presentation matches the rest of the tooling convention and does not invite interpretation errors.

---

# 7. Spindle Geometry Critique

## What appears correct

The spindle profile appears to encode the expected BP Core Burner geometry:

| Feature | Expected / implied value |
|---|---:|
| Collar diameter | 0.750 |
| Spindle root diameter | 0.375 |
| Collar height | 0.5625 |
| Spindle length | 5.625 |
| Tip diameter | about 0.1295 |
| Overall spindle length | 6.1875 |
| Collar taper | 30° |
| Spindle taper | intended 1.25° per side |

The arithmetic appears mostly right.

## What is not production-ready

The spindle view still needs the following explicitly shown or noted:

```text
UNITS
MATERIAL
FINISH
GENERAL TOLERANCE
EDGE BREAK
CONCENTRICITY / RUNOUT
TIP FACE CONDITION
COLLAR FACE REFERENCE
SHOULDER FACE REFERENCE
SPINDLE TAPER ANGLE CONVENTION
COLLAR TAPER ANGLE CONVENTION
```

## Required spindle dimensions

A production spindle drawing must include:

```text
ØA collar/body diameter
F collar height
ØD spindle root diameter
C spindle length
Ød2 spindle tip diameter
C + F overall length
E spindle taper, shown as actual small angle
G collar taper, with convention stated
centerline
```

## Recommended spindle note block

```text
SPINDLE / CORE FORMER
ØA COLLAR DIAMETER: 0.750
COLLAR HEIGHT F: 0.563
SPINDLE ROOT ØD: 0.375
SPINDLE LENGTH C: 5.625
SPINDLE TIP Ød2: 0.129
OVERALL LENGTH: 6.188
SPINDLE TAPER E: 1.25° PER SIDE
COLLAR TAPER G: 30° FROM SHOULDER FACE
ALL DIAMETERS CONCENTRIC TO CENTERLINE
```

---

# 8. Rammer Geometry Critique

## What appears correct

The rammer set appears to show four separate rammers for `H = 4`:

```text
1. Solid rammer
2. Full-depth A rammer
3. Progressive rammer 1
4. Progressive rammer 2
```

The expected overall lengths match the drawing geometry:

| Rammer | Expected OAL | Geometry appears to show |
|---|---:|---:|
| Solid rammer | 2.4375 | 2.438 rounded |
| Full-depth A rammer | 8.0625 | 8.062 / 8.063 rounded |
| Progressive rammer 1 | 6.1875 | 6.188 rounded |
| Progressive rammer 2 | 4.3125 | 4.312 / 4.313 rounded |

The bore depths appear correct:

| Rammer | Expected bore depth |
|---|---:|
| Full-depth A rammer | 5.625 |
| Progressive rammer 1 | 3.750 |
| Progressive rammer 2 | 1.875 |

The bore diameters appear correct:

| Rammer | Expected bore diameter |
|---|---:|
| Full-depth A rammer | 0.375 |
| Progressive rammer 1 | about 0.293 |
| Progressive rammer 2 | about 0.211 |

## Solid rammer critique

The solid rammer shows:

```text
OD = 0.750
head/do-not-pass station = 1.125
OAL = 2.438
```

That is coherent.

However, the drawing must define whether the horizontal line at the head station is:

```text
a scribed/engraved do-not-pass mark
a machined groove
a true shoulder
reference-only geometry
```

The user clarified that the shown groove/line is a real do-not-pass line. A machinist still needs to know **how** it is made.

## Full-depth A rammer critique

This part appears conceptually correct:

```text
OD = 0.750
head/do-not-pass station = 1.125
OAL = 8.0625
straight open-bottom cylindrical bore depth = 5.625
bore diameter = 0.375
I taper = 45° backside nozzle taper
I taper ends at bore opening
```

Problems:

```text
the angle is encoded/displayed as 225°, not 45°
the taper reference convention is not stated
the taper endpoint is not explicitly called out
the bore origin is not explicitly called out
the bore clearance is not specified
the bore edge break is not specified
```

Recommended callout:

```text
FULL-DEPTH A RAMMER
Ø0.750 OD
OAL 8.063
Ø0.375 STRAIGHT CYLINDRICAL BORE, OPEN FROM WORKING END, DEPTH 5.625
45° BACKSIDE NOZZLE TAPER FROM WORKING FACE TO Ø0.375 BORE OPENING
NO FLAT LAND AT BORE OPENING
DO-NOT-PASS MARK 1.125 FROM TOP FACE
```

## Progressive rammer critique

The progressive rammers appear correct in concept, but require explicit bore callouts.

Recommended callouts:

```text
PROGRESSIVE RAMMER 1
Ø0.750 OD
OAL 6.188
Ø0.293 STRAIGHT CYLINDRICAL BORE, OPEN FROM WORKING END, DEPTH 3.750
DO-NOT-PASS MARK 1.125 FROM TOP FACE
```

```text
PROGRESSIVE RAMMER 2
Ø0.750 OD
OAL 4.313
Ø0.211 STRAIGHT CYLINDRICAL BORE, OPEN FROM WORKING END, DEPTH 1.875
DO-NOT-PASS MARK 1.125 FROM TOP FACE
```

---

# 9. Rammer Bore Representation Critique

The hidden bore geometry appears to use vertical hidden lines plus a hidden top line. This is consistent with:

```text
straight cylindrical bore
open at the working end
flat-ended blind termination at the top of the bore
```

This matches the clarified model:

```text
All rammers have straight open-bottom cylindrical bores.
```

However, the drawing should not rely only on dashed hidden geometry. It must have explicit bore callouts.

## Required bore notes

For all hollow rammers:

```text
BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.
BORE DIAMETERS ARE FINISHED DIAMETERS.
BORE DEPTHS ARE MEASURED FROM WORKING END.
BORES CONCENTRIC TO RAMMER OD.
```

If the top of the bore must be flat:

```text
BORE DEPTH TO FLAT BOTTOM.
```

If a drill-point bottom is acceptable:

```text
DRILL POINT ACCEPTABLE BEYOND SPECIFIED FULL-DIAMETER DEPTH.
```

Do not leave this implicit.

---

# 10. Do-Not-Pass Line / Groove Critique

The current DXF appears to model the repeated rammer head line as a small one-sided V-shaped jog/notch in the rammer profile.

This is not a good representation for an axisymmetric tool.

If it is a real physical groove, it must be symmetrical and dimensioned.

If it is a real line but not a material-removing groove, it should be drawn and called out as a scribed/engraved mark, not as a profile notch.

The user clarified:

```text
The shown groove is a real do-not-pass line.
A second change-rammers line exists in practice but is not shown in the original screenshots.
```

## Recommended representation

Default production recommendation:

```text
DO-NOT-PASS MARK AT 1.125 FROM TOP FACE ON ALL RAMMERS.
SCRIBE OR ENGRAVE; DO NOT CREATE A SHOULDER.
```

If it must be a machined groove:

```text
DO-NOT-PASS GROOVE AT 1.125 FROM TOP FACE ON ALL RAMMERS.
GROOVE WIDTH: [SPECIFY]
GROOVE DEPTH: [SPECIFY]
GROOVE RADIUS: [SPECIFY]
```

Do not include a one-sided V-notch in the physical `PROFILE` outline unless that one-sided notch is truly intended, which is unlikely for a turned axisymmetric part.

## Second change-rammers line

Because the second change-rammers line exists in practice but is not in the original screenshots, the output should support two modes:

```text
LEGACY-COMPATIBLE MODE:
Second change-rammers line omitted to match original screenshots.

PRODUCTION MODE:
Second change-rammers line shown and called out as reference/mark geometry.
```

Do not silently add or omit it without a drawing note.

---

# 11. Diameter Notation Critique

The current drawing appears to show transverse dimensions like:

```text
0.750
0.375
0.293
0.211
```

but does not consistently show diameter symbols.

For turned axisymmetric parts, this is not acceptable.

Use:

```text
Ø0.750
Ø0.375
Ø0.293
Ø0.211
```

Add a general note:

```text
ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.
ALL TRANSVERSE DIMENSIONS MARKED Ø ARE DIAMETERS.
```

---

# 12. Decimal Formatting and Rounding Critique

The drawing uses values such as:

```text
.750
.375
1.125
2.438
8.062
5.625
6.188
3.750
4.312
1.875
```

This is mostly fine, but should be standardized.

Recommended production convention:

```text
Use leading zero for values less than one inch.
Use three decimal places for inch dimensions unless otherwise configured.
```

Examples:

```text
0.750
0.375
1.125
2.438
8.063
5.625
6.188
3.750
4.313
1.875
```

Note that exact halves of thousandths such as `8.0625` and `4.3125` must follow a consistent rounding policy.

Recommended:

```text
Round half up to nearest 0.001 for display, while retaining exact values internally.
```

or state the exact fractional equivalent in a table if desired.

The production drawing must include tolerance notes so rounding does not imply false precision.

---

# 13. Missing Manufacturing Notes

The current drawing lacks required shop information.

Add a production notes block:

```text
ROCKET TOOL SKETCHER — BP CORE BURNER TOOLING SET
A / TUBE I.D.: 0.750 IN
UNITS: INCHES
DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.
ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.
ALL DIAMETERS AND BORES CONCENTRIC TO CENTERLINE.
ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.
BORE DEPTHS ARE MEASURED FROM WORKING END.
DO-NOT-PASS MARK LOCATED 1.125 FROM TOP FACE OF EACH RAMMER.
BREAK ALL SHARP EDGES.
MATERIAL: [SPECIFY].
FINISH: [SPECIFY].
UNLESS OTHERWISE SPECIFIED: [ADD TOLERANCE].
```

If clearances are not baked into dimensions, add:

```text
SHOWN DIMENSIONS ARE NOMINAL DESIGN DIMENSIONS UNLESS OTHERWISE SPECIFIED.
RAMMER OD FIT RELATIVE TO TUBE I.D.: [SPECIFY].
RAMMER BORE CLEARANCE OVER SPINDLE: [SPECIFY].
SPINDLE/COLLAR FIT RELATIVE TO TUBE I.D.: [SPECIFY].
```

If dimensions are finished tooling dimensions, as clarified, use:

```text
DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.
```

---

# 14. Layer and Visual Convention Critique

The current drawing uses mostly one color in the screenshot, likely magenta. This is acceptable for a debug display but poor for production plotting.

Production drawings should distinguish:

| Entity type | Recommended treatment |
|---|---|
| Visible external edges | continuous, heavier lineweight |
| Hidden internal bores | dashed, thin lineweight |
| Centerlines | centerline linetype, thin |
| Dimension lines | thin continuous |
| Text | readable, plotted text |
| Do-not-pass marks | separate layer and explicit note |
| Construction/debug geometry | omitted from production output |

## Recommended layer names

For production DXF:

```text
RTS_VISIBLE_OUTLINE
RTS_HIDDEN_INTERNAL
RTS_CENTERLINE
RTS_DIMENSIONS
RTS_DIM_TEXT
RTS_MARKS
RTS_NOTES
RTS_TITLEBLOCK
RTS_CONSTRUCTION_DEBUG
```

For compatibility, keep names ASCII and avoid spaces.

## Lineweight recommendations

Use plotting lineweights, not just colors:

```text
Visible outline: 0.35 mm or similar
Hidden internal: 0.18 mm or similar
Centerline: 0.13-0.18 mm
Dimensions/text: 0.13-0.18 mm
Marks: 0.18 mm
```

Exact values can vary, but the hierarchy must be visible in monochrome output.

---

# 15. Linetype and Scale Risks

The file appears to mix inch units with a metric measurement flag:

```text
$INSUNITS = 1
$MEASUREMENT = 1
```

`$INSUNITS = 1` is inches. `$MEASUREMENT = 1` indicates metric defaults.

This may lead to linetype scaling oddities, especially for hidden and center lines on small inch-scale parts.

The file also appears to have:

```text
$LTSCALE = 1.0
```

On sub-inch geometry, default linetype patterns may plot poorly.

## Required checks

Validate that hidden and center lines appear correctly when:

```text
opened in a CAD viewer
printed to PDF
imported into Fusion 360 / SolidWorks / Solid Edge / FreeCAD if applicable
```

If dashed/center linetypes do not appear reliably, provide an alternate compatibility export that converts dashed lines into explicit short line segments.

---

# 16. Text and Title Critique

The part titles are too small and too close to the geometry. Some text appears clipped in the screenshot.

Current title style is inadequate for production.

Use clear part titles:

```text
PART 1 — SPINDLE / CORE FORMER
PART 2 — SOLID RAMMER
PART 3 — FULL-DEPTH A RAMMER
PART 4 — PROGRESSIVE RAMMER 1
PART 5 — PROGRESSIVE RAMMER 2
```

Add a drawing title:

```text
BP CORE BURNER TOOLING SET — A = 0.750 IN
```

Include:

```text
revision
date
scale
units
material
tolerance block
part count
```

Use text heights appropriate for plotted output.

---

# 17. Dimension Layout Critique

The drawing currently has cluttered or ambiguous dimension placement.

Problems:

```text
Head/do-not-pass dimension 1.125 appears redundantly on each rammer.
Some dimension extension lines are close to geometry and hard to associate.
The spindle angle arc is oversized and dominates the view.
The A-rammer angle dimension uses the wrong reflex angle.
Bore diameter labels are crowded near working ends.
Rightmost title/dimensions appear cropped in the screenshot.
```

Recommended dimension placement:

```text
Overall length dimensions on the right side of each part.
Bore depth dimensions on the left side or clearly offset from overall length.
OD diameter dimensions at the top of each rammer.
Bore diameter dimensions at the working end with Ø symbol.
Head/do-not-pass mark dimension shown once, then generalized by note.
Angle dimensions replaced by explicit text callouts when CAD angle entity produces reflex angles.
```

Do not duplicate dimensions unless one is explicitly marked reference.

---

# 18. Combined Sheet Layout Critique

The current drawing places all parts in a long horizontal row. This is good for formula comparison but weak as a production sheet.

The screenshot shows cropping at the right edge, which is unacceptable for release.

Recommended output modes:

## Mode 1: Combined overview sheet

Purpose:

```text
Review entire toolset.
Confirm part count.
Show relationship between spindle and rammers.
```

Include a summary table.

## Mode 2: Per-part production sheets

Purpose:

```text
Machining each part.
Clear dimensions and notes.
Reduced clutter.
```

Recommended sheets:

```text
Sheet 1: Toolset overview
Sheet 2: Spindle detail
Sheet 3: Solid rammer detail
Sheet 4: Full-depth A rammer detail
Sheet 5: Progressive rammers or one sheet per progressive rammer
```

If only one sheet is generated, include a clear part table.

Recommended table:

| Part | Name | OD | OAL | Bore Ø | Bore Depth | Taper |
|---|---|---:|---:|---:|---:|---|
| 1 | Spindle / core former | — | 6.188 | — | — | E 1.25°, G 30° |
| 2 | Solid rammer | Ø0.750 | 2.438 | none | none | none |
| 3 | Full-depth A rammer | Ø0.750 | 8.063 | Ø0.375 | 5.625 | I 45° |
| 4 | Progressive rammer 1 | Ø0.750 | 6.188 | Ø0.293 | 3.750 | none |
| 5 | Progressive rammer 2 | Ø0.750 | 4.313 | Ø0.211 | 1.875 | none |

---

# 19. DXF Header Extents Issue

The DXF header extents appear to remain placeholder values:

```text
$EXTMIN = 1e+20, 1e+20
$EXTMAX = -1e+20, -1e+20
```

Some CAD systems will recalculate this automatically. Others may open with poor zoom extents or odd import behavior.

Update the drawing extents to actual model extents before exporting.

Expected actual extents are roughly:

```text
X: -0.375 to 17.475
Y: -8.5125 to 0.700
```

Do not rely on the viewer to fix extents.

---

# 20. Compatibility Concerns

The output should be checked in multiple CAD environments, especially because the goal is clean import into common systems.

## Fusion 360

Likely issues:

```text
DXF dimensions may import as dumb sketch/text geometry.
Units can be misinterpreted if metadata and visible notes disagree.
Blocks and dimension entities may not behave parametrically.
```

Recommendation:

```text
Provide a clean per-part geometry DXF without dimensions for sketch import.
Provide a separate annotated drawing DXF/PDF for human reading.
```

## SolidWorks

Likely issues:

```text
Dimensions may import detached from geometry.
Blocks may need exploding.
Angle dimensions may preserve bad reflex values if not manually overridden.
```

Recommendation:

```text
Use simple geometry and explicit text callouts for problematic angles.
```

## Solid Edge

Likely issues:

```text
Linetypes and text may import differently.
Dimension styles may not match expected display.
```

Recommendation:

```text
Keep dimensions simple and test plotted output.
```

## FreeCAD

Likely issues:

```text
DXF importer behavior varies by workbench/settings.
Text and dimensions can be inconsistent.
Complex dimension entities may import poorly.
```

Recommendation:

```text
Simple lines, arcs, polylines, and plain text are more robust.
```

---

# 21. Recommended Output Split

The system should generate at least the following drawing/export modes.

## 21.1 Legacy comparison DXF

Purpose:

```text
Match original Flash output as closely as possible.
Useful for screenshot comparison and regression testing.
```

Characteristics:

```text
May retain original-like layout.
May show original dimension choices.
May include helper/debug annotations.
Should not be sent to machinist without production notes.
```

## 21.2 Geometry/debug DXF

Purpose:

```text
Validate formulas and derived geometry.
Use for developer inspection.
```

Characteristics:

```text
Can include construction geometry.
Can include derived dimension labels.
Can include assumption/debug overlays.
Clearly marked NOT FOR PRODUCTION.
```

## 21.3 Machinist production DXF/PDF

Purpose:

```text
Send to machinist.
```

Characteristics:

```text
Correct units and dimension scaling.
No debug reflex angles.
Proper diameter symbols.
Production notes.
Tolerances.
Material/finish placeholders or filled values.
Do-not-pass mark definition.
Bore callouts.
Readable layout.
No clipped text.
```

## 21.4 Per-part clean DXF

Purpose:

```text
CAD sketch import and machining setup.
```

Characteristics:

```text
One part per file.
Simple geometry.
Centerline included.
No cluttered sheet annotations.
Clear layer separation.
```

---

# 22. Concrete Fix Checklist for Codex

## 22.1 Dimension style fixes

- [ ] Remove or override `DIMLFAC = 100.0`.
- [ ] Set linear dimension factor to `1.0` for production drawings.
- [ ] Use actual drawing units for dimension values.
- [ ] Use three decimal places for inch dimensions by default.
- [ ] Use a consistent rounding policy.
- [ ] Add leading zero to values less than one inch.
- [ ] Add diameter symbols for transverse diameter dimensions.
- [ ] Do not rely on dimension scale tricks to mimic Flash labels.

## 22.2 Angle callout fixes

- [ ] Remove the `178.75°` / `179°` spindle taper angle from production output.
- [ ] Replace it with `SPINDLE TAPER: 1.25° PER SIDE` for BP Core Burner.
- [ ] Optionally add included taper `2.50°` if useful.
- [ ] Remove the `225°` A-rammer taper angle from production output.
- [ ] Replace it with `45° BACKSIDE NOZZLE TAPER`.
- [ ] State the angle reference convention.
- [ ] State that the taper terminates at the bore opening.
- [ ] Clarify collar taper as `30° FROM SHOULDER FACE` or use endpoint dimensions.

## 22.3 Spindle fixes

- [ ] Flip the spindle orientation or clearly label it.
- [ ] Ensure spindle presentation is consistent with legacy and/or working orientation.
- [ ] Add overall spindle length.
- [ ] Add spindle length, collar height, root diameter, tip diameter, taper angle, and collar taper callouts.
- [ ] Add centerline/concentricity note.
- [ ] Add tip face condition if production mode.

## 22.4 Rammer fixes

- [ ] Confirm all rammer OAL values display as real inches.
- [ ] Add OD diameter callouts with `Ø`.
- [ ] Add explicit bore callouts for all hollow rammers.
- [ ] State bores are straight cylindrical and open from working end.
- [ ] State bore depths are measured from working end.
- [ ] State bores are concentric to OD/centerline.
- [ ] Add bore-bottom condition if applicable.
- [ ] Define the do-not-pass line.
- [ ] Remove one-sided notch from physical profile unless intentionally specified.
- [ ] Add second change-rammers line only in production mode if requested/configured.

## 22.5 Layer and line style fixes

- [ ] Use separate production layers for visible outline, hidden internal, centerline, dimensions, text, marks, notes, and debug construction.
- [ ] Apply lineweights.
- [ ] Ensure hidden and center linetypes plot correctly at inch-scale tooling sizes.
- [ ] Provide compatibility option to render dashed lines as short explicit segments.
- [ ] Ensure construction/debug layers are off or omitted in production output.

## 22.6 Layout fixes

- [ ] Add a drawing title.
- [ ] Add readable part titles.
- [ ] Add part numbers.
- [ ] Prevent clipping of rightmost title and dimensions.
- [ ] Increase text height for plotted output.
- [ ] Add title block or notes block.
- [ ] Add a summary table.
- [ ] Reduce duplicate head/do-not-pass dimensions.
- [ ] Reduce oversized debug angle arcs.

## 22.7 Manufacturing notes

- [ ] Add visible `UNITS: INCHES` note.
- [ ] Add material placeholder or configured material.
- [ ] Add finish placeholder or configured finish.
- [ ] Add general tolerances.
- [ ] Add edge-break note.
- [ ] Add concentricity note.
- [ ] Add note that displayed dimensions are finished tooling dimensions.
- [ ] Add fit/clearance notes if configured.

## 22.8 DXF housekeeping

- [ ] Update DXF extents.
- [ ] Confirm `$INSUNITS` matches visible units.
- [ ] Avoid conflicting metric defaults in inch drawings where practical.
- [ ] Test open/zoom extents behavior.
- [ ] Test plotted PDF output.

---

# 23. Suggested Production Notes Block

Use this as a starting production notes block for the BP Core Burner example:

```text
ROCKET TOOL SKETCHER — BP CORE BURNER TOOLING SET
A / TUBE I.D.: 0.750 IN
UNITS: INCHES
DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.
ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.
ALL DIAMETERS AND BORES CONCENTRIC TO CENTERLINE.
ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.
BORE DEPTHS ARE MEASURED FROM WORKING END.
DO-NOT-PASS MARK LOCATED 1.125 FROM TOP FACE OF EACH RAMMER.
[DEFINE DO-NOT-PASS MARK AS SCRIBED, ENGRAVED, OR MACHINED GROOVE.]
BREAK ALL SHARP EDGES.
MATERIAL: [SPECIFY].
FINISH: [SPECIFY].
UNLESS OTHERWISE SPECIFIED: [ADD TOLERANCE].
```

For the full-depth A rammer:

```text
45° BACKSIDE NOZZLE TAPER ON FULL-DEPTH A RAMMER ONLY.
TAPER TERMINATES AT Ø0.375 BORE OPENING.
NO FLAT LAND AT BORE OPENING UNLESS OTHERWISE SPECIFIED.
```

For the spindle:

```text
SPINDLE TAPER: 1.25° PER SIDE.
COLLAR TAPER: 30° FROM SHOULDER FACE.
```

---

# 24. Suggested Toolset Summary Table

For BP Core Burner at `A = 0.750 in`, include a table like this:

| Part | Name | OD / Main Diameter | OAL | Bore Ø | Bore Depth | Taper / Notes |
|---|---|---:|---:|---:|---:|---|
| 1 | Spindle / Core Former | Ø0.750 collar | 6.188 | — | — | E 1.25° per side; G 30° from shoulder face |
| 2 | Solid Rammer | Ø0.750 | 2.438 | none | none | Do-not-pass mark at 1.125 |
| 3 | Full-depth A Rammer | Ø0.750 | 8.063 | Ø0.375 | 5.625 | I 45° backside nozzle taper |
| 4 | Progressive Rammer 1 | Ø0.750 | 6.188 | Ø0.293 | 3.750 | Do-not-pass mark at 1.125 |
| 5 | Progressive Rammer 2 | Ø0.750 | 4.313 | Ø0.211 | 1.875 | Do-not-pass mark at 1.125 |

---

# 25. Acceptance Criteria for Improved Machinist Drawing

A revised production drawing should pass the following checks.

## Geometry checks

- [ ] Spindle profile geometry matches expected dimensions.
- [ ] Spindle is no longer upside down, or is explicitly labeled.
- [ ] Rammer count matches `H`.
- [ ] Rammer lengths match formulas.
- [ ] Hollow rammer bore depths match formulas.
- [ ] Hollow rammer bore diameters match formulas.
- [ ] A-rammer taper applies only to first/longest rammer.
- [ ] A-rammer taper terminates at the bore opening.
- [ ] No unintended flat land appears at the A-rammer bore opening.

## Drafting checks

- [ ] Linear dimensions display in inches correctly.
- [ ] No dimensions display 100× too large.
- [ ] Diameter dimensions use `Ø`.
- [ ] Spindle taper reads `1.25° per side`, not `178.75°`.
- [ ] A-rammer taper reads `45°`, not `225°`.
- [ ] Collar taper reference convention is stated.
- [ ] Hidden bores are visually distinct from centerlines.
- [ ] Text is readable at intended sheet scale.
- [ ] No text or dimensions are clipped.
- [ ] Title block or notes block exists.
- [ ] Units, material, tolerance, finish, edge-break, and concentricity notes are present.
- [ ] Do-not-pass mark is clearly defined.

## File checks

- [ ] `$INSUNITS` matches visible unit note.
- [ ] Dimension scale factor is correct.
- [ ] Header extents are updated.
- [ ] Linetypes plot correctly.
- [ ] File opens cleanly in at least one CAD viewer.
- [ ] Exported PDF is readable in monochrome.

---

# 26. Final Assessment

The generated DXF is a good geometry/debug export, but it is **not yet a shop drawing**.

The underlying BP Core Burner geometry appears mostly correct:

```text
spindle dimensions are coherent
rammer count is correct
rammer lengths are correct
bore depths are correct
bore diameters are correct
A-rammer taper is generally in the right location
```

The key failures are drafting and manufacturing communication:

```text
spindle upside down
wrong/reflex angle callouts
100× dimension scaling risk
missing diameter symbols
ambiguous do-not-pass line
missing units/material/tolerances/finish notes
weak layer/linetype hierarchy
text too small/clipped
no title block or part table
hidden bores not explicitly called out
```

Before sending to a machinist, generate a separate production drawing mode with corrected dimension scaling, explicit manufacturing notes, proper angle callouts, clear bore definitions, readable layout, and corrected spindle orientation.

Do not use the current DXF as a production manufacturing document without revision.
