# Rocket Tool Sketcher Geometry Comparison Harness — Complete First-Pass Design

## 1. Minimal harness architecture

The harness should be a small repeatable pipeline, not a production CAD system and not a UI application.

```text
A-I parameter set
  + assumption set
  → derived geometry
  → simplified 2D side-view render
  → candidate image/vector
  + reference screenshot metadata
  → alignment
  → comparison/scoring
  → overlay/contact sheet/report
  → human decision log
```

### Minimal components

| Component | Responsibility |
|---|---|
| Parameter Registry | Stores presets/custom A-I values, units, display precision, and source. |
| Assumption Registry | Stores angle conventions and feature toggles for E, G, I, bores, and groove/no-pass marks. |
| Geometry Builder | Computes derived values and emits semantic geometry features. |
| Renderer | Draws simplified side-view geometry as geometry-only, Flash-like, overlay-ready, and per-feature renders. |
| Reference Registry | Stores screenshot paths, image sizes, crop regions, anchors, and annotations. |
| Comparator | Aligns candidate to reference and scores profile, hidden bores, taper features, markers, and optional dimensions. |
| Review Reporter | Produces overlays, difference images, score tables, and human-review notes. |

The key design choice is that geometry must retain semantics. A visible spindle line, hidden bore projection, no-pass line, dimension arrow, and centerline should not all be treated as identical strokes. Each should carry a role so it can be rendered and scored separately.

## 2. Data structures

### Input parameters

```json
{
  "id": "bp-core-burner-075in",
  "name": "BP Core Burner 0.75 in",
  "preset_key": "bp_core_burner",
  "units": "in",
  "source": "original_flash_preset_ratio_table",
  "parameters": {
    "A": 0.75,
    "B": 7.5,
    "C": 5.625,
    "D": 0.375,
    "E": 1.25,
    "F": 0.5625,
    "G": 30,
    "H": 4,
    "I": 45
  },
  "display_precision": {
    "linear_decimals": 3,
    "angle_decimals": 2
  }
}
```

### Derived geometry

Derived geometry should include values and part-feature records.

```json
{
  "parameter_set_id": "bp-core-burner-075in",
  "assumption_set_id": "baseline-e-axis-g-face-i-face-no-flat",
  "units": "in",
  "derived_values": {
    "ri": 1.125,
    "d2": 0.1295,
    "hci": 0.0818,
    "stage_step_depth": 1.875
  },
  "parts": [
    {
      "part_id": "spindle",
      "part_type": "spindle",
      "role": "core_former",
      "features": []
    },
    {
      "part_id": "rammer_01_first_longest",
      "part_type": "rammer",
      "role": "first_longest_hollow_rammer_with_backside_nozzle_taper",
      "features": []
    }
  ],
  "dimensions": [],
  "warnings": []
}
```

A feature record should look like this:

```json
{
  "feature_id": "rammer_01_bore_hidden_rect",
  "feature_type": "internal_bore_projection",
  "geometry_type": "polyline",
  "draw_role": "hidden_internal",
  "manufacturing_role": "negative_geometry",
  "points": [[0, 0], [0, 5.625], [0.375, 5.625], [0.375, 0]],
  "source_values": ["C", "D"],
  "compare_weight": 0.8,
  "notes": "Straight open-bottom cylindrical bore, shown dashed in side view."
}
```

Recommended draw roles:

```text
visible_external
hidden_internal
reference
process_marker
dimension
centerline
text
construction
```

Recommended manufacturing roles:

```text
external_geometry
negative_geometry
reference_only
process_indicator
dimension_annotation
not_manufacturing_geometry
```

### Assumption set

```json
{
  "id": "baseline-e-axis-g-face-i-face-no-flat",
  "label": "Baseline: E axis, G shoulder face, I face, no flat",
  "angle_conventions": {
    "E": "from_axis",
    "G": "from_shoulder_face",
    "I": "from_face"
  },
  "spindle": {
    "e_taper_sign": "diameter_decreases_toward_tip",
    "g_zero_mode": "square_shoulder",
    "g_profile_mode": "square_when_zero_else_flash_formula"
  },
  "rammers": {
    "bore_model": "straight_open_bottom_cylindrical",
    "bore_visibility": "hidden_dashed",
    "i_applies_to": "first_longest_rammer_only",
    "i_feature": "external_backside_nozzle_taper",
    "i_taper_end": "bore_opening",
    "i_taper_has_flat_lip": false,
    "i_taper_start_rule": "derived_from_bore_diameter_and_angle",
    "show_no_pass_line": true,
    "no_pass_line_mode": "drawn_mark_only",
    "show_second_change_line": false
  },
  "rendering": {
    "include_dimensions": true,
    "include_text_labels": true,
    "flash_like_layout": true
  }
}
```

### Reference screenshot metadata

```json
{
  "id": "ref-bp-core-burner-075in",
  "file": "references/presets/01-bp-core-burner-0.75in.png",
  "preset_key": "bp_core_burner",
  "parameter_set_id": "bp-core-burner-075in",
  "units": "in",
  "image_size_px": { "width": 1177, "height": 810 },
  "regions": {
    "spindle": { "x": 0, "y": 0, "w": 420, "h": 360 },
    "rammer_01": { "x": 0, "y": 340, "w": 360, "h": 430 }
  },
  "anchors": [
    {
      "name": "spindle_axis_start",
      "image_px": [100, 170],
      "model_ref": "spindle.axis.root"
    }
  ],
  "annotations_file": "annotations/bp-core-burner-075in.annotations.json"
}
```

## 3. Assumption toggles to test

### Fixed known truths for this pass

These should be considered fixed for this first pass:

```text
All rammers have straight open-bottom cylindrical bores.
I applies only to the first/longest rammer.
I forms the backside of the nozzle.
The I taper ends at the bore opening.
The shown groove is a real do-not-pass line.
A second practical change-rammers line exists but is not shown in the original screenshots.
Displayed dimensions are intended finished tooling dimensions.
```

### E — spindle taper angle

Test:

```text
E from axis
E from perpendicular/radial direction
E as included angle
```

Expected likely winner: `E from axis`.

### G — collar taper angle

Test:

```text
G from shoulder face using Flash formula points
G from axis
G direct conical transition between A and D
G = 0 as square shoulder
G = 0 as degenerate taper
```

Expected likely winner: Flash formula/shoulder-face convention, with `G = 0` square shoulder behavior.

### I — first/longest rammer backside nozzle taper

Test:

```text
I external backside nozzle taper, measured from working face, ending at bore opening
I external backside nozzle taper, measured from axis, ending at bore opening
I treated as included angle
I with tiny flat lip before bore opening
I as internal chamfer control candidate
```

Given the known truths, the important remaining test is angle convention and whether the screenshot implies a true flat or only pixel/stroke artifact.

### First/longest rammer taper endpoint

Test:

```text
ends exactly at bore opening
ends at a small flat before bore opening
ends at centerline apex
ends only at outer edge
```

Expected winner: ends exactly at bore opening.

### Groove/no-pass line

Test:

```text
drawn mark only
shallow physical groove
shoulder step
```

The line is known to be meaningful, but the screenshot harness should test whether Flash visually represents it as a simple drawn mark or actual side-profile geometry.

### Second change-rammers line

Test for debug only:

```text
not drawn
reference-only line
dashed process marker
```

Expected Flash-like value: not drawn.

## 4. Recommended rendering strategy

Render four outputs for each candidate:

1. **Geometry-only render** — visible outlines, hidden bores, centerlines, process marks; no text/dimensions.
2. **Flash-like sheet render** — dimensions/text/layout included, approximate original drawing.
3. **Overlay-ready render** — transparent linework for compositing onto reference screenshots.
4. **Per-feature debug render** — spindle only, I taper only, G collar only, bores only, groove only.

Use semantic layers:

```text
visible_external
hidden_internal
centerline
process_marker
dimension_line
dimension_text
reference_only
```

Use a consistent model coordinate system:

```text
Z = part axis / length direction
R = radius from centerline
side view is drawn as +R and -R around the centerline
```

Generate geometry in model coordinates first, then apply sheet layout transforms. Do not bake layout placement into geometry.

For the spindle, always render:

```text
A collar diameter
F collar height
G collar transition
D spindle/root width
C spindle length
E spindle taper
d2 derived tip width
centerline
```

For rammers, always render:

```text
outer diameter A
overall stage length
straight open-bottom cylindrical bore where applicable
first/longest rammer I taper
no-pass line at ri
```

For screenshot matching, render the no-pass line as a drawn mark by default. A physical groove candidate should be included only as a control.

## 5. Recommended comparison strategy

Use a hybrid comparison method.

### Step 1 — Manual reference preparation

For each screenshot, store:

```text
image size
preset name
units
regions of interest
alignment anchors
optional feature endpoint annotations
```

Manual region boxes are acceptable and preferable for the first pass.

### Step 2 — Candidate alignment

Use this order:

```text
manual anchor transform
bounding-box fit by part outline
edge-based local refinement
```

Avoid full-screen auto-registration because dimension text and UI chrome can dominate the match.

### Step 3 — Feature comparison

Compare each feature family separately:

| Feature family | What to compare |
|---|---|
| Outer profile | edge distance, endpoints, bounding box, taper angle |
| Hidden bores | bore width, depth, bottom position, open-bottom alignment |
| E angle | spindle taper side slope and d2 tip width |
| G angle | collar transition endpoints and shoulder shape |
| I angle | taper endpoint, taper angle, bore opening intersection |
| Groove/no-pass line | position relative to top/head section and visual representation |
| Dimensions | optional placement/presence only, not OCR-first |

## 6. Scoring method

Use feature-level scores from 0.0 to 1.0 and a weighted total.

Early geometry convention weights:

```text
outer_profile:     0.40
hidden_bores:      0.25
angle_features:    0.20
marker_groove:     0.10
dimension_layout:  0.05
```

I-focused weights:

```text
first_rammer_outer_profile: 0.30
I_taper_endpoint:           0.35
I_taper_angle:              0.20
bore_opening_agreement:     0.10
marker_groove:              0.05
```

Decision thresholds:

```text
>= 0.90       strong visual agreement
0.80–0.90     likely agreement, review target ambiguity
0.65–0.80     partial agreement, likely one bad assumption
< 0.65        likely mismatch
```

Require human review if a target ambiguity feature is below 0.85, even when total score is high.

Do not over-score:

```text
font match
anti-aliasing
arrowhead style
dash phase
title block placement
UI chrome
```

## 7. Suggested manual validation workflow

### Phase 1 — Confirm fixed truths visually

Check all presets for:

```text
one spindle plus H rammers
straight open-bottom bore projections
I only on first/longest rammer when nonzero
G=0 square shoulder
I=0 suppresses taper
no-pass line at ri = 1.5*A
second change line absent from original screenshots
```

### Phase 2 — E convention

Use:

```text
BP Core Burner
Long Winded Screamer
Strobe
Whistle Pusher
```

Compare:

```text
E from axis
E from included angle
E from perpendicular
```

Look at spindle side slope and d2.

### Phase 3 — G convention

Use nonzero-G and zero-G presets:

```text
BP Core Burner
BP End Burner
Whistle Standard
Long Winded Screamer
Stinger
Strobe
Whistle Pusher
Fountain/Gerb
```

Look at collar transition and square shoulder cases.

### Phase 4 — I convention

Use nonzero-I presets:

```text
BP Core Burner
BP End Burner
Stinger
Fountain/Gerb
```

Compare:

```text
I from face
I from axis
I with flat lip
I internal-chamfer control
```

Look at first/longest rammer working end, the bore opening, and whether any flat is actually visible.

### Phase 5 — Bore interpretation

Use multi-rammer presets:

```text
BP Core Burner
Long Winded Screamer
Strobe
Whistle Standard
Whistle Pusher
```

Check bore depth and width progression.

### Phase 6 — Groove/no-pass line

Use all presets. Compare drawn mark versus physical groove/step controls. Decide separately:

```text
Flash screenshot representation
production solid representation
```

## 8. What should be automated vs human-reviewed

### Automate

```text
preset loading
unit-aware derived values
rammer count from H
candidate geometry generation
rendering all assumption variants
alignment after manual anchors exist
feature measurement
candidate ranking
contact sheets
overlay/difference image generation
review report stubs
```

### Keep human-reviewed

```text
initial reference crop boxes
anchor placement
E/G/I endpoint annotation when needed
whether a tiny flat is real or raster artifact
whether no-pass line should become physical production groove
final acceptance/rejection of ambiguous conventions
```

### Avoid initially

```text
OCR-dependent label comparison
fully automatic screenshot segmentation
perfect Flash font/arrowhead matching
production CAD decisions based only on screenshot score
```

## Final first-pass recommendation

Use the baseline assumption set as the first candidate:

```text
E measured from axis
G measured from shoulder face / Flash formula points
G=0 produces square shoulder
I measured from working face
I applies only to first/longest rammer
I is an external backside nozzle taper
I taper ends at bore opening
no flat lip by default
straight open-bottom cylindrical bores
no-pass line drawn as mark for screenshot matching
second practical change line absent from Flash-like render
```

Then run falsification candidates for:

```text
E included angle
G from axis
I from axis
I with flat lip
no-pass line as physical groove
```

The harness should not try to decide everything from a single total score. It should produce ranked evidence and force each ambiguous convention to be accepted or rejected based on focused feature agreement across multiple presets.
