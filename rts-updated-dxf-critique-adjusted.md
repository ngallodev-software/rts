# Rocket Tool Sketcher Updated DXF Critique — Adjusted Orientation Review

## Scope

This critique reevaluates the latest generated DXF/screenshot as a drafting and manufacturing review document for the Rocket Tool Sketcher BP Core Burner tooling set.

This is not a coding review. It is a drafting, manufacturing-readiness, and geometry-interpretation critique.

This version incorporates the user correction that:

- the **spindle is now oriented correctly relative to the original Rocket Tool Sketcher artwork**;
- the **rammers are mostly correct**, except the **full-depth / full-length “A” rammer is upside down**;
- the full-depth “A” rammer is also **not using the same origin/alignment convention as the other rammers**;
- the spindle should be moved downward so its base/collar sits below the longest rammer tip, matching the original visual relationship;
- the spindle taper should be a true straight tapered side, not a series of hard stepped reductions;
- the spindle tip/root diameter labels are currently attached to the wrong ends and should be leader callouts placed off the geometry;
- the spindle needs clearer collar dimensions, including collar taper angle, collar height, and the axial height/run of the angled collar section;
- text is too crowded, overlaps or runs into neighboring parts, and is too small for a machinist-ready drawing.

## Executive assessment

The latest drawing is improving as a **formula validation and review drawing**, but it is still **not machinist-release quality**.

The most important revised finding is that the spindle should no longer be criticized as upside down. The spindle orientation now matches the original art convention. The major orientation problem is instead the **full-depth “A” rammer**, which is flipped relative to the other rammers and is not aligned to the same drawing origin/datum convention.

The largest remaining problems are:

1. The full-depth “A” rammer is upside down relative to the other rammers.
2. The full-depth “A” rammer is not aligned on the same datum/origin as the other rammers.
3. The spindle should be moved downward to match the original sheet relationship, with its base/collar below the longest rammer tip.
4. The spindle tapered section is visually resolving as hard steps rather than a clean straight taper line.
5. The spindle diameter callouts are swapped/mislocated: the small tip diameter appears at the large/root end, and the large/root diameter appears at the small/tip end.
6. Spindle diameter dimensions should be converted from on-geometry dimensions into leader callouts offset from the part.
7. The spindle is missing clear graphical dimensions for collar taper angle, collar height, and the axial height/run of the angled collar section.
8. The callout text is too small and too crowded; some notes run into the next part view.
9. Material, finish, tolerance, and clearance notes are still placeholders or absent.
10. The DXF header extents still appear uninitialized.

The arithmetic and many derived values still look broadly correct. The issue is now mostly **view convention, drawing organization, annotation placement, feature callouts, and machinist clarity**.

---

# 1. Corrections to the prior critique

## 1.1 Spindle orientation

The prior critique treated the spindle as still upside down. That should be corrected.

**Revised assessment:** the spindle is now oriented correctly relative to the original Rocket Tool Sketcher artwork.

Do not flip the spindle purely to satisfy conventional shop orientation if the goal is to preserve the original app’s visual layout. However, the drawing should make the orientation explicit so that a machinist does not confuse the collar/base end with the spindle tip.

Recommended note near the spindle:

```text
SPINDLE / CORE FORMER SHOWN IN LEGACY RTS ORIENTATION.
COLLAR / BASE END AND TIP END IDENTIFIED BY CALLOUTS.
```

or, if you do not want to mention the legacy app on a shop drawing:

```text
SPINDLE / CORE FORMER — COLLAR END SHOWN AT BASE, TIP END SHOWN OPPOSITE.
```

The current orientation is acceptable if the ends are clearly labeled.

## 1.2 Rammer orientation

The previous critique overstated the issue by saying all rammers were upside down.

**Revised assessment:** the rammers are generally oriented correctly except for the full-depth / full-length “A” rammer.

The full-depth “A” rammer appears flipped relative to the solid rammer and progressive rammers. It also does not appear to share the same origin/alignment convention. That is a serious drawing consistency issue because it makes the most important rammer—the one containing the nozzle backside taper—harder to interpret than the simpler rammers.

Required correction:

```text
Flip/reorient the full-depth “A” rammer only, so it matches the orientation and datum convention of the other rammers.
```

The full-depth “A” rammer should not be treated as a special drawing orientation unless a note explicitly says why it is different. Since it is part of the same sequential tooling set, it should be shown with the same end convention as the other rammers.

## 1.3 Rammer datum/origin alignment

The current drawing does not read as though all rammers are using a consistent origin. The expected presentation is that the rammer flat ends line up in the original direction.

That request is reasonable and standard as a drawing convention. Aligning a family of similar turned tools by a common functional datum is normal.

Recommended convention:

```text
Align all rammer flat reference ends on a common datum line.
Use that datum consistently for overall length, bore depth, and do-not-pass mark references.
```

If the flat aligned end is the non-working/handle end, call it that. If it is the working/pressing end, call it that. Avoid ambiguous terms such as “top” and “bottom” in production notes unless the sheet orientation is fixed and obvious.

---

# 2. Current drawing status by part

## 2.1 Part 1 — Spindle / core former

### What is good

The spindle is now in the expected original-art orientation. The drawing includes useful callout text for:

- collar OD;
- collar height;
- root OD;
- tip OD;
- spindle length;
- overall length;
- spindle taper angle;
- collar taper angle.

The listed values appear generally correct for BP Core Burner at `A = 0.750`:

```text
Collar OD: Ø0.750
Spindle root OD: Ø0.375
Tip OD: about Ø0.130
Spindle length: 5.625
Overall length: 6.188
Spindle taper: 1.250° per side
Collar taper: 30.000° from shoulder face
```

### Major issues

#### 2.1.1 Spindle should be moved downward in the layout

The spindle is currently placed too high relative to the rammer set. In the original Rocket Tool Sketcher drawings, the spindle sits lower, with the base/collar visually below the longest rammer tip.

This is not merely aesthetic. The legacy drawing layout communicates the relationship between the spindle and the rammer depths. The current higher placement weakens that comparison.

Recommended correction:

```text
Move the spindle downward so the spindle base/collar sits below the longest rammer tip, matching the original artwork relationship.
```

This is a layout convention, not a manufacturing geometry dimension. It should not be dimensioned as a required spatial relationship between separate tools unless it is part of an assembly view. But for the combined tooling-set sheet, it is a valid and useful visual convention.

#### 2.1.2 Spindle taper is appearing as hard steps

The spindle tapered section appears to diminish in hard steps or segmented reductions instead of a single clean straight taper line.

That is not acceptable for the production interpretation of the spindle. The spindle should be a smooth conical taper defined by the specified angle and endpoint diameters.

Required correction:

```text
Draw each spindle side as a single straight line from root diameter to tip diameter.
Do not approximate the taper with stepped or segmented reductions.
```

The correct physical interpretation is:

```text
Root diameter D at the collar/spindle transition.
Tip diameter d2 at the spindle tip.
Straight conical taper between those stations.
Taper angle E = 1.250° per side for this preset.
```

If the stepped appearance is caused by low screenshot resolution, linetype artifacts, or rendering rasterization, still test the actual DXF at high zoom. The DXF geometry should contain one clean line segment per tapered side, not multiple collinear or near-collinear segments that visually produce steps.

#### 2.1.3 Spindle diameter labels are reversed/misplaced

The small spindle tip diameter appears to be shown near the large/root end, and the larger `Ø0.375` root diameter appears to be shown near the small/tip end.

That is a critical drafting error. It can cause the spindle to be made incorrectly.

Required correction:

```text
Root OD Ø0.375 must point to the large/root end of the spindle at the collar transition.
Tip OD Ø0.130 must point to the small/tip end of the spindle.
```

Recommended callout wording:

```text
ROOT OD Ø0.375 AT COLLAR TRANSITION
TIP OD Ø0.130 AT SPINDLE TIP
```

If possible, also include the parameter names:

```text
D / ROOT OD = Ø0.375
DERIVED d2 / TIP OD = Ø0.130
```

This helps distinguish the original input `D` from the derived tip diameter `d2`.

#### 2.1.4 Spindle diameter dimensions should be leader callouts, not dimensions laid on top of the part

The small spindle diameter and root diameter should not be drawn directly over the spindle profile. On this small, tapered geometry, dimension text and arrows placed directly over the geometry make the part harder to read and can obscure the actual linework.

Recommended convention:

```text
Use leader callouts offset from the spindle.
Leader arrow points to the exact diameter station.
Text sits outside the profile, with enough spacing from neighboring parts.
```

Example:

```text
D / ROOT OD Ø0.375
→ leader points to root station at collar transition
```

```text
d2 / TIP OD Ø0.130
→ leader points to tip face
```

This is standard drafting practice and is especially appropriate for small features on a long tapered spindle.

#### 2.1.5 Missing graphical collar taper details

The spindle callout text includes collar taper information, but the drawing still needs clearer graphical dimensions for the collar region.

At minimum, the spindle drawing should show:

| Collar feature | Needed dimension/callout |
|---|---|
| Collar/base OD | `Ø0.750` |
| Collar height | `F = 0.562` |
| Collar taper angle | `G = 30.000° from shoulder face` |
| Axial height/run of angled collar taper | derived value, shown or tabulated |
| Root OD at end of collar taper | `D = Ø0.375` |
| Start and end stations of angled collar taper | clear leader or coordinate/station table |

The current drawing has total and sub-length dimensions, but the collar itself is still underdefined graphically. For a machinist, the collar region is the area most likely to be misread if it is not explicitly dimensioned.

Recommended addition:

```text
COLLAR HEIGHT F = 0.562
COLLAR TAPER G = 30.000° FROM SHOULDER FACE
COLLAR TAPER AXIAL RUN = [derived value]
```

or provide a spindle station table:

```text
STATION | AXIAL LOCATION | DIAMETER | NOTE
0       | collar/base face | Ø0.750 | base/collar OD
1       | start collar taper | Ø0.750 | start of G taper
2       | spindle root | Ø0.375 | D/root OD
3       | spindle tip | Ø0.130 | derived d2/tip OD
```

The station table may be the cleanest way to remove ambiguity from the collar geometry.

---

## 2.2 Part 2 — Solid rammer

The solid rammer appears generally correct.

Expected dimensions:

```text
OD: Ø0.750
OAL: 2.438
Do-not-pass mark: 1.125 from specified reference end
```

The current direction appears to match the other correct rammers. Keep this orientation as the reference for the full-depth “A” rammer correction.

Remaining issues:

- The do-not-pass mark should be referenced from a functional end, not merely “top face,” unless top face is the fixed drawing datum.
- Text is too close to neighboring geometry.
- The graphical diameter dimension should use `Ø0.750` visibly, not just rely on a general note.
- If the mark is a scribed mark, the drawing should avoid making it look like a machined shoulder or groove.

Recommended note:

```text
SCRIBE DO-NOT-PASS LINE 360° AROUND RAMMER, 1.125 FROM [REFERENCE END].
```

Replace `[REFERENCE END]` with either:

```text
HANDLE END
```

or:

```text
NON-WORKING END
```

or:

```text
WORKING END
```

based on the physical intent.

---

## 2.3 Part 3 — Full-depth “A” rammer

This is currently the most serious rammer problem.

### Current issue

The full-depth / full-length “A” rammer is upside down relative to the other rammers and is not aligned to the same origin.

This part should be corrected independently of the other rammers. Do not flip all rammers. The issue is with this part’s orientation and datum.

Required correction:

```text
Reorient the full-depth “A” rammer to match the solid and progressive rammers.
Place it on the same datum/origin convention as the other rammers.
Align its flat reference end with the corresponding flat ends of the other rammers.
```

### A-rammer taper

The full-depth “A” rammer is the only rammer with the `I = 45°` backside nozzle taper for BP Core Burner.

The intended relationship remains:

```text
The I taper forms the backside of the nozzle.
The taper terminates at the bore opening.
There is no flat land at the bore opening unless explicitly specified.
```

After flipping/reorienting the full-depth rammer, verify that the taper and the bore opening still meet correctly. A common failure mode here would be to flip the outer profile but leave the bore/taper feature in the old coordinate direction.

Required check after correction:

```text
45° taper is on the same end as the Ø0.375 bore opening.
The taper terminates at the Ø0.375 bore opening.
Bore depth is measured from that same working/bore-opening end.
```

### Dimension and callout needs

The full-depth rammer should show:

```text
OD Ø0.750
OAL 8.062 / 8.063 depending rounding convention
Bore Ø0.375 x 5.625 deep from working end
45° backside nozzle taper
No flat land at bore opening
Do-not-pass mark location and method
```

The drawing should explicitly state whether `45°` is measured from the working face or from the axis/centerline. Since this is a nozzle backside taper, the cleanest callout is likely:

```text
45° BACKSIDE NOZZLE TAPER FROM WORKING FACE TO Ø0.375 BORE OPENING.
```

If the actual geometry uses another convention, state that instead.

---

## 2.4 Part 4 — Progressive rammer 1

Progressive rammer 1 appears generally correct.

Expected values:

```text
OD: Ø0.750
OAL: 6.188
Bore: Ø0.293 x 3.750 deep
```

Keep the current orientation if it matches the solid rammer and original art.

Remaining issues:

- Improve text spacing.
- Use diameter symbols in visible dimensions.
- Ensure bore depth is measured from the same functional end convention used for all rammers.
- Keep hidden bore lines clean and distinguishable from centerlines.

---

## 2.5 Part 5 — Progressive rammer 2

Progressive rammer 2 appears generally correct.

Expected values:

```text
OD: Ø0.750
OAL: 4.312 / 4.313 depending rounding convention
Bore: Ø0.211 x 1.875 deep
```

Remaining issues are the same as progressive rammer 1:

- text spacing;
- explicit diameter symbols;
- consistent bore-depth datum;
- clean hidden-line convention;
- clear do-not-pass mark reference.

---

# 3. Layout critique

## 3.1 Spindle vertical placement

The spindle should be moved downward relative to the rammers.

The original Rocket Tool Sketcher artwork places the spindle so the base/collar is below the longest rammer tip. The current drawing places the spindle too high, which makes the tooling set feel visually disconnected from the original reference.

Recommended correction:

```text
Lower the spindle view so its collar/base sits below the longest rammer tip, matching the original art.
```

This is a presentation/layout correction, not a part-geometry change.

## 3.2 Rammers should share a common datum

All rammers should be drawn using a consistent datum/origin. The current issue is not that all rammers are wrong; it is that the full-depth “A” rammer breaks the convention.

Recommended convention:

```text
Use one horizontal datum line for the flat ends of all rammers.
Place solid, full-depth A, and progressive rammers on that same datum.
Dimension OAL consistently from that datum.
Dimension bore depth consistently from the working/bore-opening end.
```

If the flat end alignment is a legacy display convention rather than a manufacturing datum, that is still acceptable. Just keep it consistent.

## 3.3 Spacing between part views

The drawing still has insufficient spacing between parts and callout blocks. Text from one part runs into or visually interferes with the next part.

This is not acceptable for a machinist-ready drawing. It creates risk that a note for one part will be read as applying to the neighboring part.

Required correction:

```text
Increase horizontal spacing between part views.
Place callout blocks in reserved zones that cannot overlap adjacent geometry.
Increase text height or sheet scale.
```

Recommended minimum practice:

- Keep each part’s callout block entirely within that part’s column.
- Use leaders rather than placing text directly on geometry.
- Do not allow notes to cross into the next part’s drawing area.
- Make titles and part numbers larger than dimension text.
- Make general notes and table text large enough to read on the intended plotted sheet size.

---

# 4. Spindle geometry and drafting requirements

The spindle needs more detailed drafting than the rammers because it contains multiple transitions and two taper systems.

## 4.1 Required spindle dimensions

A machinist-ready spindle drawing should show all of the following:

| Dimension | Required? | Current status |
|---|---:|---|
| Collar OD `A` | Yes | Present, but should be leader/callout or clean diameter dimension |
| Spindle root OD `D` | Yes | Present but appears swapped/misplaced |
| Tip OD `d2` | Yes | Present but appears swapped/misplaced |
| Collar height `F` | Yes | Present in text, should also be graphically called out |
| Spindle length `C` | Yes | Present |
| Overall length `C + F` | Yes | Present |
| Spindle taper angle `E` | Yes | Present as text callout; verify leader placement |
| Collar taper angle `G` | Yes | Present in text, but missing or weak as graphical callout |
| Axial height/run of angled collar taper | Yes/recommended | Missing graphically |
| Start/end stations of collar taper | Recommended | Missing or unclear |
| Tip face condition | Recommended | Missing |
| Edge break | Required by general note | Placeholder/general only |
| Concentricity | Required by general note | Present generally, not toleranced |

## 4.2 Root and tip callout correction

The root and tip callouts should be handled as leader notes:

```text
D / ROOT OD Ø0.375
```

Leader arrow points to:

```text
large end of spindle at collar transition
```

```text
d2 / TIP OD Ø0.130
```

Leader arrow points to:

```text
small spindle tip
```

Do not draw either label over the body of the spindle.

## 4.3 Collar taper callout

The collar taper should be called out visually, not only in a text block.

Recommended leader callout:

```text
G = 30° FROM SHOULDER FACE
```

Leader points to the angled collar shoulder.

If there is room, add:

```text
COLLAR TAPER AXIAL RUN = [derived value]
```

or dimension it graphically.

## 4.4 Collar height

The collar height `F` should be graphically dimensioned near the collar, with extension lines from the collar/base face and root/taper station.

Recommended dimension:

```text
F / COLLAR HEIGHT = 0.562
```

If the collar includes a straight section plus an angled section, the drawing should distinguish:

```text
overall collar height F
height/run of angled collar portion
height/run of any straight collar portion
```

This is especially important because the Flash profile has a vertical collar/body portion followed by the angled collar taper down to `D`.

---

# 5. A-rammer orientation and taper requirements

The full-depth “A” rammer should be treated as a special geometry part, but not as a special orientation part.

It should share the same drawing convention as the other rammers.

Required full-depth A rammer corrections:

1. Flip/reorient it to match the other rammers.
2. Move it so its flat reference end aligns with the other rammer flat ends.
3. Ensure the bore opens from the correct working end.
4. Ensure the `45°` taper is located at the bore opening.
5. Ensure the `45°` taper terminates at the bore opening.
6. Confirm that there is no small flat at the bore opening unless explicitly specified.
7. Ensure the do-not-pass mark is referenced from the same functional end convention as the other rammers.

Recommended callout:

```text
45° BACKSIDE NOZZLE TAPER ON FULL-DEPTH A RAMMER ONLY.
TAPER TERMINATES AT Ø0.375 BORE OPENING.
NO FLAT LAND AT BORE OPENING.
```

Recommended bore callout:

```text
Ø0.375 STRAIGHT CYLINDRICAL BORE x 5.625 DEEP FROM WORKING END.
```

If the rammer is shown in legacy orientation and the working end is not visually obvious, add:

```text
WORKING / BORE-OPENING END IDENTIFIED BY LEADER.
```

---

# 6. Do-not-pass mark critique

The current drawing says the do-not-pass line is a scribed 360° mark. That is much better than earlier versions.

However, the note still uses “top face,” which becomes fragile when views can be flipped.

Recommended replacement:

```text
SCRIBE DO-NOT-PASS LINE 360° AROUND EACH RAMMER, 1.125 FROM [FUNCTIONAL REFERENCE END].
```

Use one of the following after confirming physical intent:

```text
1.125 FROM HANDLE END
```

or:

```text
1.125 FROM NON-WORKING END
```

or:

```text
1.125 FROM WORKING END
```

Avoid:

```text
1.125 FROM TOP FACE
```

unless the top face is intentionally the formal drawing datum.

If the line is scribed/engraved and not a groove, add:

```text
SCRIBE / ENGRAVE MARK ONLY; DO NOT MACHINE SHOULDER OR RELIEF GROOVE.
```

If it is a physical groove, then the drawing must specify groove width and depth. Without those values, a machinist cannot make it consistently.

---

# 7. Text and annotation critique

## 7.1 Text is too small

The text appears too small for a production drawing. It may be readable while zoomed in, but it will be poor on a plotted sheet or printed PDF.

Recommended correction:

```text
Increase part title and callout text height.
Use larger title text than note text.
Use consistent text size hierarchy.
```

Suggested hierarchy:

| Text type | Relative size |
|---|---:|
| Drawing title | largest |
| Part titles | large |
| Callout labels | medium |
| Dimension text | medium |
| Table text | medium/small, but still readable |
| General notes | medium |

## 7.2 Text overlaps neighboring parts

Some callout blocks run into the next drawing. This is a drafting defect.

Recommended correction:

```text
Reserve a rectangular annotation zone for each part.
Prevent annotation zones from overlapping adjacent part columns.
Increase part spacing.
```

If the combined sheet becomes too wide, split into multiple sheets or use a table-heavy overview plus individual detail sheets.

## 7.3 Use leaders instead of text over geometry

For small spindle diameters and collar features, use leaders. Do not place labels directly over the tapered profile.

This is standard drafting practice and is not a nonstandard request.

---

# 8. Notes and table critique

## 8.1 General notes are useful but still incomplete

The drawing has important notes such as:

```text
UNITS: INCHES
DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.
ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.
ALL TRANSVERSE WIDTH DIMENSIONS ACROSS CENTERLINE ARE DIAMETERS.
ALL DIAMETERS AND BORES CONCENTRIC TO CENTERLINE.
ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.
BORE DEPTHS ARE MEASURED FROM WORKING END.
SCRIBE DO-NOT-PASS LINE 360 DEG AROUND EACH RAMMER.
BREAK ALL SHARP EDGES.
```

These are directionally good.

But placeholders remain:

```text
MATERIAL: SPECIFY
FINISH: SPECIFY
UNLESS OTHERWISE SPECIFIED: ADD TOLERANCE.
```

Those placeholders must be replaced before machinist release.

## 8.2 Add orientation-specific notes only where needed

Since the spindle orientation is intentionally legacy-correct, add a clear note rather than changing it.

Suggested note:

```text
SPINDLE SHOWN IN LEGACY RTS ORIENTATION; COLLAR / BASE AND TIP IDENTIFIED BY CALLOUTS.
```

For the rammers, after fixing the full-depth A rammer, use a global note:

```text
ALL RAMMERS SHOWN IN SAME ORIENTATION WITH FLAT REFERENCE ENDS ALIGNED.
```

If the working ends are aligned instead, say that instead.

## 8.3 Add a spindle station table

The table is useful, but the spindle is complex enough to justify its own station table.

Recommended table:

```text
SPINDLE STATIONS
STATION | FEATURE | DIAMETER | AXIAL LOCATION / LENGTH | NOTE
1 | collar/base OD | Ø0.750 | — | tube ID reference
2 | collar taper start | Ø0.750 | — | start of G taper
3 | spindle root | Ø0.375 | F = 0.562 from base/collar reference | D/root OD
4 | spindle tip | Ø0.130 | C = 5.625 from root | derived d2
```

Exact station wording depends on the chosen spindle datum.

---

# 9. DXF technical critique

## 9.1 Units and dimension scale

The DXF now appears to use inches and real dimension values. The previous dimension-scale issue appears fixed.

Current technical status observed in the DXF:

```text
$INSUNITS = 1     // inches
$DIMLFAC = 1.0   // no 100x dimension scaling
$DIMDEC = 3      // three decimal places
```

That is good.

## 9.2 Extents are still not updated

The DXF header still appears to contain placeholder extents:

```text
$EXTMIN = 1e+20, 1e+20, 1e+20
$EXTMAX = -1e+20, -1e+20, -1e+20
```

This can cause bad zoom extents or awkward import behavior in some CAD systems.

Required correction:

```text
Update DXF extents before export/release.
```

## 9.3 Diameter symbol portability

The DXF uses AutoCAD-style `%%c` in some text strings. That may display correctly in AutoCAD-compatible tools, but some importers may show it literally.

Recommended correction:

- Use actual Unicode `Ø` where supported;
- or test `%%c` in Fusion 360, SolidWorks, Solid Edge, and FreeCAD;
- always include a plotted PDF where the symbols are confirmed visible.

## 9.4 Layering

Layer separation appears improved. Keep separate layers for:

```text
PROFILE
HIDDEN
CENTER
DIM
TEXT
TITLE
MARKS
NOTES
TABLE
```

For production plotting, also verify lineweight and linetype behavior in monochrome output.

---

# 10. What you are asking for that is standard vs nonstandard

## 10.1 Standard drafting requests

The following requests are standard and appropriate:

- using leader callouts for small spindle diameters;
- moving labels off the part geometry;
- increasing spacing so text does not overlap neighboring views;
- increasing text size;
- aligning similar rammers on a common datum;
- keeping a family of related tools in consistent orientation;
- showing collar height and collar taper angle clearly;
- showing the axial height/run of the angled collar section;
- calling out root and tip diameters at the correct ends;
- drawing the spindle taper as a clean straight line rather than stepped segments;
- adding clear orientation notes where legacy orientation differs from normal shop convention;
- adding a spindle station table or equivalent coordinate table.

None of these are unusual for a machinist-ready drawing.

## 10.2 Potentially nonstandard or legacy-specific requests

The following are not “wrong,” but they should be documented because they are more about preserving the original app layout than pure manufacturing drafting:

### Spindle moved down to match original art

Moving the spindle downward so its base sits below the longest rammer tip is a valid legacy-layout convention. It helps visually compare the toolset against the original Flash drawing.

However, it is not a manufacturing relationship between separate parts unless explicitly presented as an assembly/process diagram. In a production drawing, it should be treated as layout only.

Recommended note if needed:

```text
PART VIEWS ARRANGED TO MATCH LEGACY RTS TOOLING LAYOUT; RELATIVE VIEW POSITIONS ARE NOT ASSEMBLY DIMENSIONS.
```

### “Do-not-pass” terminology

“Do-not-pass line” is understandable in this tooling context, but it may not be a standard machine-shop term by itself. It is fine if defined.

Recommended note:

```text
DO-NOT-PASS LINE = SCRIBED 360° REFERENCE MARK; DO NOT MACHINE SHOULDER OR GROOVE UNLESS SPECIFIED.
```

or, if it is a groove:

```text
DO-NOT-PASS GROOVE = MACHINED 360° GROOVE, WIDTH ___, DEPTH ___.
```

### Legacy orientation

Showing the spindle in the original app orientation is acceptable. If a machinist expects a different orientation, clear end labels solve the problem.

Recommended note:

```text
VIEWS ARE ORIENTED TO MATCH LEGACY RTS DRAWING CONVENTION. USE CALLOUTS AND DIMENSIONS AS AUTHORITY.
```

---

# 11. Clarifying questions for the next revision

These are not blockers for the critique, but they should be answered before final machinist-release drawings.

1. **For rammer alignment:** which flat ends should line up—the handle/non-working ends, or the working/bore-opening ends?

2. **For the full-depth “A” rammer:** when it is flipped to match the other rammers, should the `45°` nozzle backside taper remain visually at the same physical working end as the bore opening?

3. **For the do-not-pass line:** is it a scribed/engraved line only, or a machined groove? If it is a groove, what width and depth should be used?

4. **For do-not-pass datum:** should the mark be measured from the handle/non-working end, from the working end, or simply from the top face in legacy drawing orientation?

5. **For the spindle collar:** do you want the angled collar taper’s axial height/run displayed as a driven dimension, a reference dimension, or only included in a station table?

6. **For spindle diameter labels:** should the drawing explicitly label the root diameter as `D` and the tip diameter as derived `d2` to avoid confusion?

7. **For production notes:** what material, finish, linear tolerance, angular tolerance, OD fit/clearance, and bore clearance should be used?

8. **For output package:** should the combined sheet remain visually close to the original Flash output, with separate machinist detail sheets generated afterward, or should the combined sheet itself become the machinist-ready drawing?

---

# 12. Required changes before machinist release

## Must fix

1. Keep the spindle orientation as currently shown if it matches the original art, but label collar/base end and tip end clearly.
2. Move the spindle downward so its base/collar sits below the longest rammer tip, matching the original image layout.
3. Redraw the spindle tapered sides as clean straight lines at the specified taper angle, not as hard steps.
4. Correct the swapped/misplaced spindle diameter labels:
   - `Ø0.375` belongs at the large/root end near the collar transition;
   - `Ø0.130` belongs at the small/tip end.
5. Convert spindle root and tip diameter dimensions into leader callouts placed away from the part.
6. Add graphical callouts/dimensions for:
   - collar height `F`;
   - collar taper angle `G`;
   - axial height/run of the angled collar portion.
7. Reorient the full-depth “A” rammer only so it matches the other rammers.
8. Place the full-depth “A” rammer on the same datum/origin alignment as the other rammers.
9. Verify the full-depth “A” rammer’s `45°` taper remains at the bore-opening/working end after reorientation.
10. Increase spacing between part views so text does not run into the next drawing.
11. Increase text size or use a larger sheet/detail sheets.
12. Replace material, finish, and tolerance placeholders with real values.
13. Add bore bottom condition if the bore termination shape matters.
14. Update DXF extents.
15. Confirm diameter symbols render correctly in target CAD systems.

## Should fix

1. Add a spindle station table.
2. Add part numbers large enough to read at plotted scale.
3. Add a view/layout note stating that relative part placement follows legacy RTS layout and is not an assembly dimension.
4. Replace “top face” with a functional reference for do-not-pass marks.
5. Add explicit clearance notes or state that dimensions are finished nominal dimensions without clearance allowance.
6. Provide a plotted PDF alongside the DXF.
7. Split into a combined overview sheet plus detail sheets if the combined sheet remains crowded.

---

# 13. Final revised assessment

The drawing is moving in the right direction, but the next revision should focus on geometry presentation and drafting clarity rather than adding more text.

The spindle orientation should now be accepted as correct relative to the original art. The main spindle issues are not orientation; they are layout height, taper line quality, swapped/misplaced diameter labels, missing collar-region dimensions, and annotation crowding.

The rammers should mostly remain as they are, except for the full-depth/full-length “A” rammer, which needs to be flipped/reoriented and placed on the same datum convention as the other rammers. Because that rammer carries the `I = 45°` backside nozzle taper, it is critical that the taper remain at the bore opening after correction.

The most important next-pass requirements are:

```text
Move spindle down to match original layout.
Keep spindle orientation as original-art correct.
Make spindle taper a clean straight taper.
Fix root/tip diameter callouts and move them off geometry.
Add collar height, collar taper angle, and collar taper axial run.
Flip/reorigin only the full-depth A rammer.
Align all rammer flat ends consistently.
Increase text size and spacing.
Replace placeholder production notes.
```

Once those are fixed, the drawing will be much closer to a machinist-quality production document.
