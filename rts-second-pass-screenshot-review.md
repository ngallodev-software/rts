# Rocket Tool Sketcher — Second-Pass Screenshot-Driven Review

## Scope

This is a critical, screenshot-driven review of the current Rocket Tool Sketcher interpretation. I am treating the screenshot package as evidence and trying to confirm, challenge, or refine the model rather than assuming the current interpretation is correct.

This review focuses only on tooling interpretation, drawing behavior, manufacturing meaning, and ambiguity. It does not discuss application code, UI frameworks, or implementation architecture.

The most important correction from this second pass is:

> **The nonzero `I` taper is strongly supported as a real external taper, but it does not appear to belong to the solid/final rammer. It appears on the full-depth hollow rammer, likely the legacy-named “A rammer.”**

That changes the previous interpretation materially.

---

## 1. Strong confirmations from the screenshots

### 1.1 Statement-by-statement confirmation table

| Current statement | Screenshot support level | Review |
|---|---:|---|
| The leftmost tapered part is a real external spindle/core former. | **Strongly supported** | Every preset shows the leftmost part as a separate tapered spindle-like part with real dimensions for collar/base diameter, spindle root diameter, tip diameter, spindle length, collar height, and taper angles. The helper images for spindle length and spindle width also depict this part as a physical spindle. |
| The vertical parts are separate physical rammers, not alternate views of one part. | **Strongly supported** | The vertical parts are laid out side-by-side as separate drawn parts with different overall lengths and different hidden/internal regions. The spacing and dimensioning are consistent with separate tools in a set, not alternate views. |
| `H` truly controls the number of separate rammer parts. | **Strongly supported** | Presets with `H = 2` show two vertical rammers; presets with `H = 3` show three; presets with `H = 4` show four. BP End Burner, Stinger, and Fountain/Gerb show two. Whistle, Whistle Pusher, Strobe, and Custom show three. BP Core Burner and Long Winded Screamer show four. |
| The dashed rectangles inside rammers are real internal blind bores. | **Strongly supported, with wording nuance** | The dashed rectangles track the spindle-clearance dimensions: full-depth rammers show dashed regions of depth `C` and diameter `D`; later rammers show shallower regions and smaller diameters. They are hidden-line style interior geometry. The nuance is that they are also process/reference indicators of spindle engagement. |
| The dashed rectangles are not just reference/process overlays. | **Somewhat to strongly supported** | They are not merely decorative overlays because their dimensions are mechanically necessary for a rammer to pass over the spindle. However, the Flash drawing style does not prove whether the bore bottom/opening is represented with full manufacturing detail. Best interpretation: real internal geometry shown using simplified hidden/reference drafting. |
| Later rammers are sequential depth-specific tooling parts. | **Strongly supported** | In `H = 3` and `H = 4` presets, later rammers have progressively shorter overall lengths, shorter dashed internal regions, and smaller lower/internal diameters. This matches sequential compaction around a tapered spindle. |
| The top repeated rammer section of length `1.5*A` is a real geometric feature, not just a drawing marker. | **Somewhat supported, not proven** | The `1.125"` section appears on every rammer when `A = 0.75"`, matching `1.5*A`. But the outer diameter above and below appears the same, so the section may be a reference/witness region rather than a true shoulder. The little crease is visually present but undimensioned. |
| Nonzero `I` represents a real tapered working-end geometry on the final/“A” rammer. | **Partly supported, partly contradicted** | Nonzero `I` clearly represents a real external working-end taper, but the screenshots contradict the idea that it belongs to the solid/final rammer. It appears on the full-depth hollow rammer, not the solid rammer. |
| `G = 0` means square collar shoulder geometry. | **Strongly supported** | Whistle Pusher and Fountain/Gerb have `G = 0` and show a square collar/spindle transition instead of the sloped collar shoulder seen in `G > 0` presets. |
| Presets are fully representable by `A-I` plus a few simple zero-value special cases. | **Mostly supported, with one important mismatch** | The geometry shown is largely explained by `A-I`, `G = 0`, `I = 0`, and `H`. However, Long Winded Screamer appears to contradict the provided ratio table for `B`. Also, the applicability of `I` must be corrected: it belongs to the full-depth hollow “A rammer,” not the solid rammer. |

---

## 2. Challenges to the current model

### 2.1 The largest challenge: `I` is not on the solid/final rammer

The screenshots strongly challenge the current statement:

> Nonzero `I` is an external taper on the solid/final/“A” rammer.

The better interpretation is:

> **Nonzero `I` is an external working-end taper on the full-depth hollow rammer, which is probably what the original app calls the “A rammer.”**

Evidence:

- **BP Core Burner, `H = 4`, `I = 45°`:** the 45° taper is on the long full-depth hollow rammer, not on the short solid rammer and not on the later shallower rammers.
- **BP End Burner, `H = 2`, `I = 30°`:** the solid rammer is untapered; the hollow rammer has the 30° working-end taper.
- **Stinger, `H = 2`, `I = 35°`:** the solid rammer is untapered; the hollow rammer has the 35° working-end taper.
- **Fountain/Gerb, `H = 2`, `I = 40°`:** the solid rammer is untapered; the hollow rammer has the 40° working-end taper.
- **All `I = 0` presets:** the corresponding full-depth hollow rammer has a flat/square lower end instead of that conical/nosed taper.

So the screenshots strongly support `I` as a real machined taper, but they contradict the earlier placement of that taper on the solid/final rammer.

### 2.2 The “A rammer” is probably not the solid rammer

The UI label says:

```text
'A' rammer taper
```

The screenshots suggest the original app’s “A rammer” is not the solid rammer. It is more likely the **first hollow rammer used over the spindle**, meaning the full-depth rammer with:

```text
total length = rb2 = B - F + ri
internal depth = C
internal diameter = D
```

This is the rammer that receives the `I` taper when `I` is nonzero.

### 2.3 The head/crease section is not proven to be physical geometry

The repeated upper section of each rammer is consistently dimensioned as `1.5*A`, so the length reference is real in the drawing logic. But the screenshots do not prove that the visible crease is a required machined groove or shoulder.

Reasons:

- The upper and lower rammer sections appear to have the same outside diameter `A`.
- The crease/notch has no width, depth, radius, or tolerance.
- It appears stylistically identical across all rammers and presets.
- It may be a visual divider between “head/witness” and “working” portions rather than a physical relief.

Best manufacturing interpretation: **dimension `ri = 1.5*A` is real/reference-critical; the notch/groove is not production geometry unless separately specified.**

### 2.4 Long Winded Screamer has a likely preset-table mismatch

The Long Winded Screamer screenshot at `A = 0.75"` shows:

```text
Tube length B = 6"
Spindle length C = 4.071"
Spindle width D = 0.429"
Collar height F = 0.268"
H = 4
I = 0
```

Those displayed rammer lengths match `B = 6"`, not `B = (7.25 / 0.875) * A`.

If `A = 0.75"`, the provided ratio table gives:

```text
(7.25 / 0.875) * 0.75 = 6.214"
```

But the screenshot shows `6"`, and the shown rammer lengths also agree with `B = 6"`:

```text
ra2 = 6 - (4.071 + 0.268) + 1.125 = 2.786"
rb2 = 6 - 0.268 + 1.125 = 6.857"
```

Those are exactly the visible values in the screenshot. Therefore the Long Winded Screamer `B` ratio in the working table is probably wrong, or there is a version mismatch between the decompiled table and the screenshot.

---

## 3. Best interpretation of E, G, and I

### 3.1 `E` — spindle taper

**Best interpretation:** `E` is the side taper angle of the spindle relative to the spindle axis/centerline.

**Confidence:** High.

**Screenshot evidence:**

- Every spindle drawing places the `E` angle label along the long tapered spindle section.
- The label appears next to the spindle side wall, not at the collar shoulder and not at the rammer.
- The visual taper is very shallow for values like `1°`, `1.25°`, `1.5°`, and `2°`, which is consistent with a side angle from the vertical axis.
- The derived tip diameter shown in the screenshots matches the formula:

```text
d2 = D - 2*C*tan(E)
```

That formula only makes sense if `E` is the side angle from the spindle axis, not an included cone angle and not an angle from the horizontal face.

**Helper-image evidence:** Moderate. The helper image named for spindle taper is not as clear as the preset drawings. Some helper captures appear offset or mismatched to adjacent fields. The preset drawings and formula are stronger evidence than the helper image alone.

**Drafting implication:** Label as:

```text
Spindle taper E, per side, from tool axis
```

or avoid ambiguity by giving `D`, `d2`, and `C` plus the angle.

### 3.2 `G` — collar taper

**Best interpretation:** `G` is the angle of the collar shoulder taper, most likely measured from the horizontal/radial shoulder face rather than from the vertical spindle axis.

**Confidence:** Moderate-high.

**Screenshot evidence:**

- In presets where `G > 0`, the spindle collar has a sloped shoulder from diameter `A` down to diameter `D`.
- The `G` angle label is drawn at the collar shoulder region.
- In presets where `G = 0`, specifically Whistle Pusher and Fountain/Gerb, the collar shoulder becomes square/flat with no sloped shoulder.
- The visual angle mark at the collar is placed like a shoulder/ramp angle, not like a long-axis taper angle.

**Formula evidence:** The spindle profile equation effectively uses:

```text
axial shoulder rise = ((A - D) / 2) * tan(G)
```

That supports `G` behaving like an angle from a horizontal/radial shoulder reference.

**Helper-image evidence:** Moderate. The helper image for collar height clearly shows the collar region; the helper image for collar taper is less clear and may be visually shifted/mismatched. The preset drawings are more reliable.

**Drafting implication:** Do not simply label `G = 30°` without context. Use one of:

```text
Collar shoulder taper G, measured from horizontal shoulder face
```

or give explicit endpoint coordinates for the shoulder taper.

### 3.3 `I` — “A” rammer taper

**Best interpretation:** `I` is the external working-end taper angle on the full-depth hollow rammer, probably the original app’s “A rammer.” It appears to be measured from the lower horizontal working face/base line to the tapered outside flank.

**Confidence:** High that it is external; moderate-high on exact angle reference; moderate on exact taper construction endpoints.

**Screenshot evidence:**

- The helper image for `I` clearly shows a rammer with an external tapered/nosed lower end and an angle marker drawn between the sloped side and a horizontal base/reference line.
- BP Core Burner shows `45°` on the bottom of the full-depth hollow rammer.
- BP End Burner shows `30°` on the bottom of the full-depth hollow rammer.
- Stinger shows `35°` on the bottom of the full-depth hollow rammer.
- Fountain/Gerb shows `40°` on the bottom of the full-depth hollow rammer.
- Presets with `I = 0` show no corresponding external lower taper on the full-depth hollow rammer.

**Most likely construction:**

```text
The taper begins at the outer rammer body diameter A near the lower working end.
The taper ends at a flat lower nose/opening of diameter D.
The taper angle is I.
The full-depth internal dashed region remains tied to C and D.
```

**What `I` appears to change:**

- It changes the lower external working-end shape of the full-depth hollow rammer.
- It determines the axial length of the tapered nose when combined with `A` and `D`.
- It does not appear to change the overall rammer length formula.
- It does not appear to change the internal dashed depth `C`.
- It does not appear to apply to later shallower rammers.
- It does not appear to apply to the solid rammer.

**Still ambiguous:**

- Whether the angle is formally measured from horizontal or from the rammer axis. The helper and annotation style suggest horizontal, but the original code would settle this.
- Whether the taper ends exactly at diameter `D` in all cases or merely at the current full-depth bore diameter. In screenshots, those appear to coincide.
- Whether the taper is intended to form a conical external nose only, or whether it is also meant to shape the pressed composition/nozzle region in a more specific way.
- Whether the internal bore in the tapered end is open, flat-bottomed, or simplified in the side view.

---

## 4. Best interpretation of dashed rammer interiors

### 4.1 What the screenshots show

The dashed regions appear as centered internal rectangular zones inside hollow rammers. They vary by stage:

- The full-depth hollow rammer has a dashed region with depth `C` and diameter `D`.
- Later hollow rammers have progressively shallower dashed regions and progressively smaller diameters.
- Solid rammers do not show dashed interiors.
- The dashed region starts at the lower working end of the rammer and extends upward by the relevant spindle-clearance depth.

Examples:

- Strobe: full-depth rammer shows a `3"` dashed region at `Ø0.375"`; later rammer shows a `1.5"` dashed region at approximately `Ø0.323"`.
- BP Core Burner: full-depth rammer shows a `5.625"` dashed region at `Ø0.375"`; later stages show `3.75"` at `Ø0.293"` and `1.875"` at `Ø0.211"`.
- Whistle Standard: full-depth rammer shows `1.5"` at `Ø0.375"`; later stage shows `0.75"` at `Ø0.323"`.

### 4.2 Candidate interpretations

#### Interpretation A: true blind cylindrical bore

**Support level:** Strong.

Evidence:

- Dashed-line convention normally indicates hidden internal geometry.
- The dimensions match exactly what a rammer would need to clear the spindle.
- The decreasing bore depth and decreasing bore diameter match the progressively exposed spindle profile during sequential compaction.
- Without such internal clearance, the hollow rammers could not physically pass over the spindle.

Manufacturing consequence:

> The dashed rectangle should become a real internal negative volume in 3D solids.

#### Interpretation B: projected spindle engagement zone

**Support level:** Strong as a secondary meaning.

Evidence:

- The dashed region dimensions are not arbitrary; they correspond to the portion of spindle each rammer must clear at that stage.
- The dashed regions function visually as an engagement-depth diagram.
- The app may be showing the “spindle occupancy” region inside the rammer rather than drafting every manufacturing detail of the bore.

Manufacturing consequence:

> Even if it is drawn as an engagement reference, it still implies real clearance geometry.

#### Interpretation C: process reference overlay only

**Support level:** Weak by itself.

Evidence against this being only an overlay:

- The dashed region is dimensioned by diameter and depth.
- It appears only in rammers that need spindle clearance.
- It changes predictably with the spindle taper formula.
- It corresponds to necessary material removal.

Best conclusion:

```text
The dashed rectangle is both a process/reference depiction and a real internal bore requirement.
```

### 4.3 Should the dashed rectangles affect 3D solid generation?

**Yes.**

The dashed rectangles should generate internal subtracted geometry in any 3D manufacturing model. The safest 3D interpretation is:

```text
A centered internal cylindrical clearance bore from the working end,
with depth = stage spindle-clearance depth,
and diameter = stage spindle-clearance diameter.
```

For full-depth hollow rammer:

```text
bore depth = C
bore diameter = D
```

For later stages:

```text
bore depth = C - j * C/(H - 1)
bore diameter = D - j * hci
```

### 4.4 What remains unclear about the dashed bore

The screenshots do not fully define:

- bore bottom shape: flat-bottomed, drill-point, or idealized square-bottom;
- clearance over the spindle;
- whether the bore is truly cylindrical or only minimum clearance envelope;
- whether later bores should be straight cylinders or tapered to match the spindle;
- how the bore intersects the external `I` taper on the full-depth hollow rammer.

However, the drawing uses simple rectangular hidden geometry, so the most Flash-faithful interpretation is **straight cylindrical bore**, not a matching tapered internal bore.

---

## 5. Best interpretation of the rammer head/crease section

### 5.1 What the screenshots show

Every rammer has a repeated upper section dimensioned as:

```text
1.125" when A = 0.75"
```

That exactly equals:

```text
1.5 * A
```

Each rammer also shows a small visual crease/notch at the transition between the upper section and the longer lower body.

### 5.2 Is the visual notch a physical geometry break?

**Screenshot support:** Somewhat supported, not proven.

The notch looks like a physical crease in the linework, but it is not dimensioned. The drawing does not provide:

- groove width;
- groove depth;
- groove radius;
- chamfer angle;
- shoulder diameter change;
- tolerance;
- note saying it is a cut, stop, or handle feature.

Also, the upper and lower sections both appear to be `ØA`, so there is no clearly dimensioned shoulder diameter difference.

### 5.3 Best manufacturing interpretation

The length `ri = 1.5*A` is definitely part of the drawing logic and should remain visible as a reference/witness/head section.

The physical crease itself should **not** be modeled by default as a required machined groove. It should be treated as one of the following until better evidence appears:

1. a visual divider between head and working length;
2. a witness mark showing the `ri` boundary;
3. an optional shallow groove if the modern system lets the user explicitly enable and dimension it.

### 5.4 Would I model the crease in a 3D solid by default?

No.

For manufacturing solids, I would model the rammer body as a clean cylinder unless the groove is separately specified. I would preserve the `ri` section as a drawing/reference dimension, and optionally include a non-manufacturing reference mark in drawings.

### 5.5 Does any screenshot imply the crease must be a real machined groove?

No screenshot proves that. It is repeated and visually obvious, but the lack of dimensions makes it unsuitable as mandatory production geometry.

---

## 6. Preset-specific exceptions or rules

### 6.1 Rules strongly supported by screenshots

#### Rule: `H` controls number of rammers

Strongly supported.

```text
H = 2 → two rammers
H = 3 → three rammers
H = 4 → four rammers
```

#### Rule: `G = 0` suppresses collar taper and creates square shoulder geometry

Strongly supported.

Seen in:

- Whistle Pusher
- Fountain/Gerb

These show the spindle rising from a square collar shoulder, unlike the sloped collar shoulders in `G > 0` presets.

#### Rule: `I = 0` suppresses the external taper on the full-depth hollow rammer

Strongly supported.

Seen in:

- Whistle Standard
- Whistle Pusher
- Long Winded Screamer
- Strobe
- Custom Whistle example

The corresponding full-depth hollow rammer has a square/flat lower end rather than a conical/nosed taper.

#### Rule: `I > 0` creates external taper on full-depth hollow rammer

Strongly supported.

Seen in:

- BP Core Burner, `I = 45°`
- BP End Burner, `I = 30°`
- Stinger, `I = 35°`
- Fountain/Gerb, `I = 40°`

### 6.2 Rules not supported

#### Rule: `I` applies to the solid/final rammer

Contradicted.

The solid rammer remains untapered in all nonzero-`I` screenshots. The taper is on the full-depth hollow rammer.

#### Rule: later partial-depth rammers inherit `I`

Not supported.

BP Core Burner has `H = 4` and `I = 45°`, but only the full-depth hollow rammer has the 45° external taper. The later partial-depth rammers do not show that taper.

### 6.3 Preset-specific geometry beyond A-I?

The screenshots do not reveal preset-specific geometry rules beyond:

```text
G = 0 → square collar shoulder
I = 0 → no A-rammer external taper
I > 0 → full-depth hollow/A-rammer external taper
H → number of rammers
```

No preset appears to require a unique geometry engine. The observed differences are explainable through parameter values and zero-value behavior.

The one exception is not geometry but data consistency: **Long Winded Screamer appears to use a different `B` value than the provided ratio table.**

---

## 7. Inconsistencies / version mismatches / suspicious cases

### 7.1 Long Winded Screamer — likely `B` mismatch

This is the clearest mismatch.

The provided ratio table says:

```text
B = (7.25 / 0.875) * A
```

For `A = 0.75"`, this gives:

```text
B = 6.214"
```

But the screenshot shows:

```text
Tube length = 6"
```

The visible rammer lengths match `B = 6"`, not `6.214"`.

With screenshot values:

```text
A = 0.75
B = 6
C = 4.071
D = 0.429
F = 0.268
ri = 1.125
```

Derived:

```text
solid rammer length = 6 - (4.071 + 0.268) + 1.125 = 2.786"
full-depth hollow length = 6 - 0.268 + 1.125 = 6.857"
```

Those match the Long Winded Screamer screenshot.

Therefore, one of the following is likely true:

1. the preset table transcription for Long Winded Screamer `B` is wrong;
2. the decompiled logic and screenshot are from different versions;
3. the app uses a special Long Winded Screamer tube length override;
4. the visible screenshot was generated after a custom edit to `B` while retaining the preset name.

Because the right-side preset selector still shows Long Winded Screamer and the `B` field is greyed out like a preset value, the simplest conclusion is:

> **Long Winded Screamer likely uses `B = 8*A`, at least in this SWF/screenshot version.**

### 7.2 BP End Burner — supports corrected `I` interpretation

BP End Burner is not inconsistent internally. It is important because it falsifies the “solid rammer taper” interpretation.

The solid rammer has no `I` taper. The hollow rammer has `I = 30°` taper.

### 7.3 Stinger — supports corrected `I` interpretation

Stinger also falsifies the “solid rammer taper” interpretation.

The solid rammer has no taper. The hollow rammer has the `35°` external taper.

### 7.4 Fountain/Gerb — confirms both `G = 0` and corrected `I`

Fountain/Gerb is useful because it combines:

```text
G = 0
I = 40°
H = 2
```

The spindle collar shoulder is square, supporting the `G = 0` rule.

The hollow rammer has the 40° external taper, supporting the corrected `I` rule.

### 7.5 BP Core Burner — confirms stage progression and corrected `I`

BP Core Burner shows four rammers:

1. solid/short rammer;
2. full-depth hollow rammer with `I = 45°` external taper;
3. partial-depth hollow rammer;
4. shorter partial-depth hollow rammer.

This confirms:

- `H = 4` means four rammers;
- later stages are progressive depth variants;
- `I` does not apply to all hollow stages;
- `I` does not apply to the solid rammer.

### 7.6 Whistle Pusher — confirms `G = 0` square shoulder and `I = 0` suppression

Whistle Pusher shows:

```text
G = 0
I = 0
```

The spindle collar is square-shouldered.

The full-depth hollow rammer has a flat/square lower end, not a tapered/nosed working end.

### 7.7 Rounding discrepancies

Minor decimal differences across screenshots are consistent with normal display rounding. Examples include:

- `0.5625"` displayed as `0.563"`;
- derived diameters like `0.1297"` displayed as `0.13"`;
- derived diameters like `0.3226"` displayed as `0.323"`.

These are not concerning.

---

## 8. Remaining ambiguities

### 8.1 Exact geometric construction of the `I` taper

High confidence:

```text
I creates an external taper on the full-depth hollow/A rammer.
```

Still ambiguous:

- Is `I` measured from the horizontal working face or from the vertical axis?
- Does the taper always terminate at diameter `D`?
- Does the taper intersect an open bore or a blind bore bottom?
- Is the taper axial length calculated solely from `A`, `D`, and `I`?
- Does the taper create a functional compaction/nozzle profile beyond simply clearing the spindle?

The helper image strongly suggests `I` is measured from a horizontal base/reference line, but production drafting should state this explicitly.

### 8.2 Exact meaning of “A rammer”

The screenshots imply the “A rammer” is the full-depth hollow rammer, not the solid rammer. However, the app does not label each rammer directly in the drawing.

Recommended terminology in the modern interpretation:

```text
A rammer = full-depth hollow rammer with optional I taper
Solid rammer = short solid rammer with no bore
Later rammers = progressive partial-depth hollow rammers
```

This naming should be verified against any original documentation if available.

### 8.3 Dashed bore bottom and opening condition

The dashed rectangle tells us there is internal clearance, but not the precise machining method. Unknowns:

- flat-bottom bore vs drilled point;
- exact bottom shape;
- open-end edge/chamfer;
- clearance allowance;
- whether dashed lines represent actual bore walls or only spindle engagement envelope.

For Flash-faithful geometry, treat it as a straight cylindrical clearance region. For production, add explicit bore-bottom and clearance notes.

### 8.4 Head/crease geometry

The `1.5*A` head length is strongly supported. The notch/groove is not.

Unknowns:

- whether the crease is intended as a physical groove;
- groove width;
- groove depth;
- whether it is only a visual divider;
- whether the upper section is meant to indicate striking/handling/above-tube length.

### 8.5 Spindle collar marker/small feature

Some spindle drawings show small local details near the collar transition. The screenshots support the larger collar/taper geometry, but they do not prove that every tiny drawn mark is a separate manufacturable feature.

### 8.6 Tolerances and clearances

The screenshots show nominal dimensions only. They do not define:

- rammer OD clearance relative to tube I.D.;
- spindle clearance relative to rammer bores;
- fit class;
- material;
- surface finish;
- edge breaks;
- concentricity;
- perpendicularity;
- runout.

Any machinist-ready drawing must add these.

---

## 9. Final confidence-ranked conclusions

### 9.1 High-confidence conclusions

1. **The leftmost part is a physical spindle/core former.**

2. **The vertical parts are separate physical rammers.**

3. **`H` controls the number of rammers shown.**

4. **Later rammers are separate sequential depth-specific compaction tools.**

5. **The dashed rectangles are internal spindle-clearance regions and should affect 3D solid generation as negative/internal geometry.**

6. **The dashed rectangles also function as process/reference indicators, because they show how much spindle each rammer clears.**

7. **`G = 0` produces a square collar shoulder.**

8. **`I = 0` suppresses the external taper on the full-depth hollow/A rammer.**

9. **`I > 0` creates a real external tapered working end on the full-depth hollow/A rammer.**

10. **The earlier interpretation that `I` applies to the solid/final rammer is contradicted by the screenshots.**

11. **The Long Winded Screamer screenshot contradicts the provided `B = (7.25 / 0.875) * A` ratio. The screenshot supports `B = 8*A` for `A = 0.75"`.**

### 9.2 Moderate-confidence conclusions

1. **`I` is probably measured from the horizontal lower working face/base line to the external taper flank.**

2. **The `I` taper probably starts at the full outside diameter `A` and ends at a lower flat/opening diameter equal to `D`.**

3. **The dashed internal region is most likely a straight cylindrical bore, not a tapered bore matching the spindle profile.**

4. **The `1.5*A` rammer head section is a real reference/witness/head length, but not necessarily a separate physical shoulder.**

5. **The visible crease at the rammer head boundary is probably a visual divider or optional witness groove, not mandatory production geometry.**

6. **`G` is probably measured from a horizontal/radial shoulder reference, not from the spindle axis.**

### 9.3 Speculative conclusions

1. The upper rammer section may be a striking/handling region intended to remain above the tube mouth during use.

2. The full-depth hollow “A rammer” taper may form a specific pressed composition/nozzle transition rather than only being a clearance/entry shape.

3. The original drawing order may not be the actual use order. The use order is likely deepest/full-depth hollow rammer first, then progressively shallower rammers, then solid rammer.

4. Some helper screenshots appear visually shifted or duplicated relative to field names, so the helper image set may not be perfectly reliable for E/G/H/I without the preset drawings.

### 9.4 Revised working model after screenshot review

The revised interpretation should be:

```text
A = tube I.D.
B = tube length datum
C = spindle length
D = spindle root width / full-depth bore diameter / A-rammer nose diameter
E = spindle side taper from axis
F = collar height
G = collar shoulder taper; G = 0 gives square shoulder
H = number of separate rammers
I = external working-end taper on the full-depth hollow “A rammer”; I = 0 suppresses it
```

Parts:

```text
Spindle/core former:
  Real external revolved geometry defined by A, C, D, E, F, G, and d2.

Solid rammer:
  OD A, length B - (C + F) + ri, head/reference length ri.
  No normal bore and no I taper in observed screenshots.

Full-depth hollow / A rammer:
  OD A, length B - F + ri, internal region depth C and diameter D.
  If I > 0, has external tapered working end terminating near diameter D.

Later hollow rammers:
  OD A, progressively shorter total length, progressively shallower internal region,
  progressively smaller internal/lower diameter.
  They do not appear to inherit I taper.
```

### 9.5 What should change from the prior interpretation

The prior model should be updated in three main ways:

1. **Move `I` from the solid/final rammer to the full-depth hollow/A rammer.**

2. **Treat the `1.5*A` head length as real/reference-critical, but treat the visual crease/groove as non-mandatory unless dimensioned.**

3. **Flag Long Winded Screamer `B` as a likely preset-table/version mismatch.**

Everything else in the current model is broadly supported by the screenshot package.
