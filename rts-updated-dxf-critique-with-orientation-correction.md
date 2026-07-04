# Updated DXF critique — Rocket Tool Sketcher tooling set

## User correction / orientation addendum

The spindle is still upside down. In addition, the rammers are now all upside down. The expected drafting orientation is that the rammers’ flat ends should all line up and remain in the original Rocket Tool Sketcher direction. This correction supersedes any wording below that treats the current rammer orientation as potentially acceptable with only a note. The production drawing should reorient the rammers, not merely label them.

---

# Original critique text, unchanged

This version is **substantially improved** over the earlier DXF. It now looks much closer to a real manufacturing drawing: units are visible, notes were added, part callouts were added, the table is helpful, the bad `179°` / `225°` angle dimensions appear to have been replaced with text callouts, and the dimension scaling problem appears corrected in the DXF.

That said, I would still **not send this to a machinist as-is**. It is now a good review/proof drawing, but it still has several shop-critical ambiguities and a few technical contradictions.

## Major improvements since the prior version

The DXF now has several strong upgrades:

| Area | Improvement |
|---|---|
| Units | DXF `$INSUNITS` is inches, and the drawing has a visible `UNITS: INCHES` note. |
| Dimension scaling | The previous dangerous `100×` dimension factor appears fixed; `$DIMLFAC = 1.0`. |
| Angle display | The bad reflex angle dimensions are no longer the dominant callouts. The spindle taper is now called out as `1.250 DEG PER SIDE`, and the A-rammer taper as `45.000 DEG BACKSIDE NOZZLE TAPER`. |
| Notes | General manufacturing notes were added. |
| Table | A part summary table was added. This is a major readability improvement. |
| Layers | The file uses separate layers for profile, hidden, center, dimensions, notes, table, and marks. |
| A-rammer taper | The full-depth A rammer now clearly shows a taper running to the bore opening, which matches the current interpretation. |

So the generator is moving in the right direction.

---

## Critical remaining issues

## 1. The spindle orientation is still problematic

The spindle is still shown with the collar/body at the top and the long tapered spindle extending downward.

You already noted the earlier spindle was upside down. This version still needs an explicit orientation decision. The drawing text says:

```text
SHOWN COLLAR END DOWN
```

But the actual drawn geometry appears to show the **collar at the top**, not down. That is an internal contradiction.

This needs to be fixed before machinist release.

Use one of these, but do not mix them:

```text
SPINDLE SHOWN COLLAR END UP / TIP DOWN
```

or:

```text
SPINDLE SHOWN WORKING END DOWN
```

or flip the spindle to match the legacy Rocket Tool Sketcher orientation and remove the confusing note.

As drafted, the spindle orientation note does not match the displayed geometry.

---

## 2. Rammer “working end” orientation is ambiguous

The rammer bores and the A-rammer taper appear to open from the **top** of the drawn rammers.

For example, in the DXF geometry, the full-depth A-rammer bore runs from the top face downward by `5.625`, and the 45° taper is also at the top face.

That may be fine if the drawing convention is:

```text
WORKING END SHOWN AT TOP
```

But previous language has used “open-bottom” bores. If “bottom” means the lower end on the drawing, then the current rammers are upside down. If “bottom” means the practical working end regardless of drawing orientation, then the drawing must say that.

Add a direct orientation note near the rammers:

```text
RAMMERS SHOWN WORKING END UP.
BORE DEPTHS MEASURED FROM WORKING END.
```

or reorient the rammers so the working end is visually at the bottom.

Right now the note “bore depths are measured from working end” is good, but the drawing does not make the working end visually unambiguous enough.

---

## 3. The do-not-pass mark location is inconsistent

This is the biggest geometry/drafting contradiction I found.

The notes say:

```text
DO-NOT-PASS MARK LOCATED 1.125 FROM TOP FACE OF EACH RAMMER.
```

But the actual `MARKS` layer lines in the DXF appear to be located **1.125 from the working/bottom end**, not 1.125 from the top face.

Examples from the DXF geometry:

| Rammer | OAL | Mark Y location | What that implies |
|---|---:|---:|---|
| Solid rammer | `2.4375` | `-1.3125` | `2.4375 - 1.125 = 1.3125`, so mark is 1.125 from lower end |
| Full-depth A rammer | `8.0625` | `-6.9375` | `8.0625 - 1.125 = 6.9375`, so mark is 1.125 from lower end |
| Progressive 1 | `6.1875` | `-5.0625` | 1.125 from lower end |
| Progressive 2 | `4.3125` | `-3.1875` | 1.125 from lower end |

So either the **note is wrong** or the **mark geometry is wrong**.

This must be resolved.

If the do-not-pass mark is supposed to be 1.125 from the top face, draw it at:

```text
Y = -1.125
```

on every rammer.

If it is supposed to be 1.125 from the working end, revise the note to:

```text
DO-NOT-PASS MARK LOCATED 1.125 FROM WORKING END OF EACH RAMMER.
```

At the moment, the drawing gives conflicting instructions.

---

## 4. The do-not-pass mark is still not manufacturable as specified

The note now says:

```text
DO-NOT-PASS MARK SHOWN AS REFERENCE BAND ON DRAWING.
```

But earlier you clarified that the shown groove/line is real. A machinist still needs to know how to make it.

“Reference band” is not enough if the mark is intended to exist on the finished tool.

Specify one of these:

```text
SCRIBE DO-NOT-PASS LINE, 360° AROUND RAMMER.
```

or:

```text
ENGRAVE DO-NOT-PASS LINE, 360° AROUND RAMMER.
```

or:

```text
MACHINE GROOVE, WIDTH ___, DEPTH ___, 360° AROUND RAMMER.
```

If it is only a visual drafting aid, then keep it on a reference layer and say:

```text
REFERENCE ONLY — DO NOT MACHINE.
```

The current wording sits between those two interpretations and is still not shop-clear.

---

## 5. Diameter notation is improved in notes/table, but not enough in dimensions

The notes and table use `%%c` for diameter symbols, such as:

```text
OD %%c0.750
BORE %%c0.375
```

That is good in AutoCAD-style DXF, though some importers may show `%%c` literally.

However, the graphical dimension callouts still appear as plain linear dimensions like:

```text
0.75
0.375
0.293
0.211
```

For a turned, axisymmetric part drawing, those should be explicitly diameter dimensions:

```text
Ø0.750
Ø0.375
Ø0.293
Ø0.211
```

At minimum, add a strong general note:

```text
ALL TRANSVERSE WIDTH DIMENSIONS ACROSS CENTERLINE ARE DIAMETERS.
```

Better: override the dimension text for diameter dimensions so the visible drawing itself shows `Ø`.

---

## 6. Spindle table row is too simplified

The table currently lists the spindle with:

```text
OD Ø0.750
OAL 6.188
Notes E 1.250 / G 30.000
```

That is not enough for the spindle.

The spindle is not simply an `OD Ø0.750` part. It has:

```text
collar OD Ø0.750
root OD Ø0.375
tip OD Ø0.130
collar height 0.562
spindle length 5.625
overall length 6.188
spindle taper 1.250° per side
collar taper 30° from shoulder face
```

The individual spindle callout text includes most of this, but the table row is too compressed. A machinist using the table as the primary reference could miss the root/tip diameters.

Recommended: either add a separate spindle station table, or change the spindle row to something like:

```text
SPINDLE | COLLAR Ø0.750 | ROOT Ø0.375 | TIP Ø0.130 | OAL 6.188 | E 1.250°, G 30°
```

---

## 7. Text and annotations are still too small and dense

The screenshot shows the drawing is very wide, with many small text callouts clustered near the parts. The added notes are useful, but the drawing now risks being hard to read unless plotted very large.

The worst areas are:

- callout text beside the full-depth A rammer;
- callout text beside progressive rammer 1;
- the far-right notes/table area;
- title labels above the parts.

For a machinist package, this should probably become either:

1. a combined overview sheet plus individual detail sheets, or  
2. a larger sheet with better part spacing and a formal title block.

The current combined view is good for review, but still cramped for production.

---

## 8. Hidden bore lines are better, but their convention still needs tightening

The hidden bore geometry is now more readable and the notes say:

```text
ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.
BORE DEPTHS ARE MEASURED FROM WORKING END.
```

That is good.

Still, the hidden lines and centerlines are visually similar in the screenshot, especially because the centerlines are green and the hidden lines are also not strongly differentiated.

For production output:

| Geometry | Recommended treatment |
|---|---|
| Visible profile | black, continuous, heavier |
| Hidden bore | black/gray, dashed, thin |
| Centerline | centerline pattern, thin |
| Do-not-pass mark | separate mark layer, clear note |
| Construction/reference | omitted from production drawing |

The current layer separation is structurally good, but plotting behavior should be tested in monochrome PDF.

---

## 9. Header extents are still not updated

The DXF still appears to have placeholder extents:

```text
$EXTMIN = 1e+20, 1e+20
$EXTMAX = -1e+20, -1e+20
```

Some CAD systems will recalculate this automatically, but others may open to a bad zoom or import awkwardly.

Update extents before release.

---

## 10. Font/style portability risk

The DXF includes several font/style definitions, including OpenSans and Liberation font names. If the receiving CAD system does not have those exact font files, text may substitute unpredictably.

For machinist DXF exchange, prefer a very basic CAD-safe text style, or include a PDF alongside the DXF as the authoritative plotted drawing.

Also, `%%c` diameter notation is common in AutoCAD-style text, but not every importer displays it correctly. For maximum portability, test the file in the target CAD systems or use both:

```text
Ø0.750
```

and a fallback note.

---

## 11. Notes still contain placeholders

The drawing now has:

```text
MATERIAL: SPECIFY
FINISH: SPECIFY
UNLESS OTHERWISE SPECIFIED: ADD TOLERANCE.
```

That is useful as a reminder, but it means the drawing is still not machinist-ready.

Before sending out, replace those placeholders with real values.

At minimum:

```text
MATERIAL: [actual material]
FINISH: [actual finish]
UNLESS OTHERWISE SPECIFIED: .XXX ± ___, ANGLES ± ___
```

Also add clearances if these dimensions are finished tooling dimensions but still need slip/clearance fits:

```text
RAMMER OD CLEARANCE RELATIVE TO TUBE I.D.: ___
BORE CLEARANCE OVER SPINDLE: ___
```

If the drawing intentionally gives finished nominal dimensions with no extra clearance, state that clearly.

---

# Geometry review

## Spindle

The spindle numeric geometry appears coherent for BP Core Burner:

```text
A = 0.750
D = 0.375
C = 5.625
F = 0.562
d2 ≈ 0.130
OAL = 6.188
E = 1.250° per side
G = 30° from shoulder face
```

The main problems are not arithmetic. They are:

- orientation ambiguity;
- incorrect “collar end down” note;
- table row too compressed;
- lack of a proper station table;
- missing production tolerances/finish/material.

## Solid rammer

The solid rammer geometry appears numerically correct:

```text
OD = 0.750
OAL = 2.438
head / mark reference = 1.125
```

The open issue is the do-not-pass mark: location and manufacturing method need correction.

## Full-depth A rammer

This part is much improved.

The drawing now supports the intended interpretation:

```text
OD = 0.750
OAL = 8.062
bore = Ø0.375 x 5.625 deep
straight cylindrical bore
45° backside nozzle taper
taper terminates at Ø0.375 bore opening
no flat land
```

The biggest remaining issue is orientation: visually, the bore/taper open from the top of the drawn part. If that is intended, label the working end at the top. If not, flip the part.

## Progressive rammers

The progressive rammer geometry appears correct:

```text
Progressive 1:
OD = 0.750
OAL = 6.188
bore = Ø0.293 x 3.750 deep

Progressive 2:
OD = 0.750
OAL = 4.312
bore = Ø0.211 x 1.875 deep
```

Again, the do-not-pass mark location appears inconsistent with the note.

---

# Remaining must-fix list before sending to a machinist

1. Resolve orientation convention for spindle and rammers.
2. Correct or remove the contradictory spindle note:
   ```text
   SHOWN COLLAR END DOWN
   ```
3. Resolve do-not-pass mark location:
   - from top face, or
   - from working end.
4. Define the do-not-pass mark manufacturing method:
   - scribed,
   - engraved,
   - machined groove,
   - or reference only.
5. Add diameter symbols to graphical dimension callouts, not just notes/table.
6. Replace material, finish, and tolerance placeholders with actual values.
7. Add fit/clearance notes if the OD and bores are finished dimensions.
8. Update DXF extents.
9. Increase text size or split into separate detail sheets.
10. Add a clearer spindle station table.
11. Test hidden/centerline appearance in monochrome plot output.
12. Verify `%%c` diameter text displays correctly in Fusion 360, SolidWorks, Solid Edge, and FreeCAD, or use a safer representation.

---

# Final assessment

This updated DXF is a strong step forward. It fixes several of the dangerous issues from the first pass, especially the dimension scale problem and the bad reflex angle callouts.

The underlying geometry now looks mostly correct for the BP Core Burner preset. The full-depth A rammer taper is represented much more clearly, and the bore/depth table is a major improvement.

However, it still has **three shop-critical problems**:

1. **orientation ambiguity**, especially spindle and rammer working ends;
2. **do-not-pass mark contradiction**, because the note says one location while the drawn mark appears at another;
3. **incomplete manufacturing specification**, because material, finish, tolerances, clearances, and mark method remain placeholders or undefined.

I would classify this as:

```text
Good formula-validation / review DXF.
Nearly usable drafting prototype.
Not yet a machinist-release drawing.
```
