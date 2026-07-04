# 04 — Recommended Rendering Strategy

## Guiding rule

Render the simplest side-view geometry that can answer the interpretation questions.

Do not try to perfectly clone every Flash text placement, anti-aliasing artifact, or UI border at first. The first pass should compare geometry, not graphic polish.

## Coordinate model

Use a consistent model coordinate system before mapping to screen pixels.

Recommended model coordinates:

```text
Z axis = part length axis
R axis = radial distance from centerline
Side-view full diameter is drawn as +R and -R around centerline.
Units are the same as the parameter set.
```

For per-part profile generation:

```text
Z = 0 at the working end or spindle base datum, depending on part type.
R = 0 at centerline.
Positive and negative R are mirrored for full side-view display.
```

For Flash-like sheet layout:

```text
Generate each part in model coordinates.
Apply rotate/translate/layout transforms afterward.
Do not bake sheet placement into geometry calculations.
```

## Geometry layers for rendering

Render these semantic layers separately so they can be compared independently:

```text
visible_external
hidden_internal
centerline
process_marker
dimension_line
dimension_text
reference_only
```

This allows the comparator to score outer geometry without being confused by dimension lines, or score hidden bores without being confused by text.

## Candidate render types

Generate at least four render products per candidate:

### 1. Geometry-only render

Contents:

```text
visible_external
hidden_internal
centerline
process_marker
```

No dimensions or text. This is the best input for automated geometric comparison.

### 2. Flash-like render

Contents:

```text
visible_external
hidden_internal
centerline/process markers
dimension lines
text labels
rough original layout
```

This is for human review against the original screenshot.

### 3. Per-feature debug render

Draw one feature category at a time:

```text
spindle only
first/longest rammer only
all rammer bores only
I taper only
G collar taper only
groove/no-pass lines only
```

This is critical when two full-sheet candidates look similar but differ in the ambiguous feature.

### 4. Overlay-ready render

Use transparent background and exact candidate linework. This is composited over the reference screenshot after alignment.

## What to render for the spindle

Always render:

```text
A collar/body diameter
F collar height
G collar transition
D spindle/root width
C spindle length
E spindle taper
d2 derived tip width
centerline
```

For comparison variants, render one candidate per `E` and `G` convention.

## What to render for rammers

Always render:

```text
outer diameter A
overall length per stage
straight open-bottom cylindrical bore for hollow rammers
bore diameter/depth per stage
first/longest rammer I taper
no-pass line at ri
```

Optional debug render:

```text
second practical change-rammers line, reference-only, not included in Flash-like comparison by default
```

## Treatment of the dashed rectangles

For Flash-like rendering, draw the bore projection as dashed hidden geometry.

For geometry-only render, include the hidden bore lines on their own layer. Do not omit them. They are now known to represent actual open-bottom cylindrical bores, even if their screenshot appearance is also process/reference-like.

## Treatment of the groove / no-pass line

Render the shown groove as a line/mark by default in the screenshot harness.

Reason: the current truth says it is a real do-not-pass line, but the screenshot harness is trying to match the Flash drawing. A physical groove model would add extra visible side-profile edges that may not be present in the reference screenshot.

Recommended comparison candidates:

```text
A. drawn mark only
B. shallow groove, exaggerated for detection
C. shoulder step, falsification candidate
```

If B or C clearly mismatches every screenshot, keep the production solid decision separate from Flash screenshot matching.

## Layout strategy

Use two layout modes:

### Flash-like sheet layout

Goal: compare complete sheet to complete screenshot.

This should approximate original positions and rotations:

```text
spindle left/top region
rammers placed in the same relative sheet positions as the preset screenshot
text/dimensions optional
```

### Normalized per-part layout

Goal: compare individual parts independent of sheet placement.

Each part gets:

```text
same local origin
same scale
same margin
same orientation
```

Per-part layout is the better tool for deciding `E`, `G`, and `I`.

## Avoid OCR dependency

Text labels and dimensions can be included for visual review, but the automated scoring should not depend on OCR. Instead, compare the generated numeric dimensions to known expected/displayed values from the parameter set and use manually annotated label boxes only where necessary.
