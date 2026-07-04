# 05 — Comparison Strategy and Scoring

## Comparison philosophy

Pixel comparison alone is too fragile because the Flash screenshots include anti-aliasing, UI chrome, text, arrows, and possibly inconsistent image scaling. The harness should use a hybrid approach:

```text
1. Feature-aware geometric comparison
2. Edge/pixel comparison inside known regions
3. Human overlay review
```

## Step 1: Reference preparation

For each screenshot, create metadata with:

```text
image size
preset name
units
regions of interest for spindle and each rammer
manual alignment anchors
optional feature annotations
```

Do not try to infer every region automatically at first. Manual region boxes are cheap and reliable.

## Step 2: Candidate normalization

For each candidate/reference pair:

1. Crop the reference to the relevant region.
2. Render the candidate in the same local orientation.
3. Align candidate to reference using anchor points or bounding boxes.
4. Scale candidate using known dimension references where possible, usually `A`, `B`, `C`, or total part length.
5. Compare only after alignment.

Recommended alignment methods, in order:

```text
manual anchor transform
bounding-box fit by part outline
edge-based local refinement
```

Avoid full-image auto-registration at first because dimensions/text can dominate the fit.

## Step 3: Feature-specific comparisons

### A. Outer profile score

Compares visible external linework.

Use:

```text
edge distance / chamfer distance
endpoint distance
bounding-box difference
angle difference for tapered features
```

Best for:

```text
spindle external geometry
collar taper G
first/longest rammer I taper
overall rammer lengths
```

### B. Hidden bore score

Compares dashed/internal bore projection.

Use:

```text
bore rectangle endpoint error
bore width error
bore depth error
bore bottom position error
dash-pattern-insensitive line overlap
```

Important: compare the underlying ideal bore lines, not the exact dash phase.

### C. Angle score

For `E`, `G`, and `I`, compute:

```text
expected rendered angle vs annotated/reference angle
endpoint agreement for the angled segment
intersection agreement with adjacent features
```

For `I`, endpoint agreement is more important than raw angle because the core ambiguity is where the taper begins/ends.

### D. Marker/groove score

Compare:

```text
line position relative to top/striking end
line position relative to total rammer length
whether it appears as a single mark or real groove geometry
```

This should be low weight in early passes because marker rendering can be stylistic.

### E. Dimension-layout score

Optional, low-weight.

Compare:

```text
dimension arrow locations
dimension extension line positions
presence/absence of key labels
not text OCR
```

Use this to validate drawing compatibility, not to decide physical geometry.

## Recommended total score weights

For early geometry convention testing:

```text
outer_profile:       0.40
hidden_bores:        0.25
angle_features:      0.20
marker/groove:       0.10
dimension_layout:    0.05
```

For `I`-focused runs:

```text
first_rammer_outer_profile: 0.30
I_taper_endpoint:           0.35
I_taper_angle:              0.20
bore_opening_agreement:     0.10
marker/groove:              0.05
```

For `G`-focused runs:

```text
spindle_collar_outer_profile: 0.45
G_angle_endpoint_agreement:   0.25
shoulder_square/transition:   0.20
dimension_layout:             0.10
```

For `E`-focused runs:

```text
spindle_taper_profile:     0.45
d2_tip_width_agreement:    0.25
spindle_length_agreement:  0.15
angle_annotation_location: 0.15
```

## Candidate decision thresholds

Suggested first-pass thresholds:

```text
score >= 0.90: strong visual agreement
0.80–0.90: likely agreement, review ambiguous features
0.65–0.80: partial agreement, candidate may have one bad assumption
< 0.65: likely mismatch
```

Feature-level override:

Even if total score is high, mark candidate as `needs_human_review` if any target ambiguity feature scores below threshold:

```text
E feature < 0.85 in E-focused run
G feature < 0.85 in G-focused run
I feature < 0.85 in I-focused run
hidden bore feature < 0.85 in bore-focused run
```

## Human-review artifacts

For each candidate, generate:

```text
candidate geometry-only render
candidate Flash-like render
reference crop
candidate/reference overlay
difference image
feature score table
one-page review markdown
```

## What not to over-score

Do not over-weight:

```text
anti-aliased stroke thickness
text label exact font
arrowhead style
dash phase
title block placement
UI chrome
```

Those can be tuned later and should not decide geometry conventions.

## Comparison output summary

The final output of a run should be a ranked table like:

```text
Preset                Candidate            Total  E     G     I     Bore  Decision
BP Core Burner         baseline-v01         .88   .94   .91   .79   .90   review I
BP Core Burner         I-from-axis          .72   .94   .91   .42   .90   reject I
BP Core Burner         I-with-flat-lip      .83   .94   .91   .70   .90   weaker than baseline
Stinger                baseline-v01         .90   .93   .89   .86   .92   accept likely
```
