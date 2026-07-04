# 01 — Minimal Harness Architecture

## Purpose

The harness should render candidate geometry under competing interpretation assumptions, compare those candidates against original Flash screenshots, and produce enough evidence to decide the ambiguous conventions before the CAD model is locked.

The harness should be deliberately small. It only needs enough structure to make comparisons repeatable.

## Core pipeline

```text
Parameter Set A-I
      ↓
Assumption Set
      ↓
Derived Geometry Builder
      ↓
2D Renderer
      ↓
Candidate Render
      ↓
Reference Screenshot + Metadata
      ↓
Alignment / Normalization
      ↓
Feature + Pixel Comparison
      ↓
Score Report + Contact Sheet
      ↓
Human Review Decision
```

## Minimal components

### 1. Parameter Registry

Holds presets and custom parameter sets.

Responsibilities:

- Store `A` through `I`.
- Store units.
- Store preset name and source.
- Store whether values are original/preset/custom.
- Optionally store known displayed/rounded values from screenshots.

### 2. Assumption Registry

Holds named geometry interpretation variants.

Responsibilities:

- Define angle conventions for `E`, `G`, and `I`.
- Define first/longest rammer taper behavior.
- Define whether groove/no-pass mark is visual only or physical.
- Define whether the second practical change-rammer line is drawn in candidate renders.
- Define visibility of hidden/internal geometry.

### 3. Geometry Builder

Converts one parameter set plus one assumption set into normalized 2D part geometry.

Responsibilities:

- Compute derived values: `ri`, `d2`, `hci`, stage lengths, bore depths, bore diameters.
- Generate spindle visible exterior profile.
- Generate rammer visible exterior profiles.
- Generate internal bore/hidden geometry for rammers.
- Generate groove/no-pass line features.
- Generate dimension feature records separately from physical geometry.

Important: the builder should retain feature semantics. A line should not merely be a line; it should know whether it is `visible_external`, `hidden_internal`, `reference`, `dimension`, `centerline`, or `marker`.

### 4. 2D Renderer

Renders the derived geometry to a simple image or vector candidate.

Responsibilities:

- Draw visible outlines, hidden bores, centerlines, markers, and optional dimensions.
- Use consistent stroke widths and linetypes.
- Support Flash-like side-view layout.
- Support per-part isolated rendering for focused comparisons.
- Support output as SVG and/or raster PNG.

### 5. Reference Registry

Stores metadata for original screenshots.

Responsibilities:

- Reference file path.
- Preset name.
- Units.
- Screenshot pixel dimensions.
- Crop/region information.
- Manual anchors for alignment.
- Optional feature annotations.

### 6. Comparator

Compares a candidate render with a reference screenshot.

Responsibilities:

- Align candidate to reference.
- Compare outer profiles.
- Compare hidden/internal bores.
- Compare taper endpoints/angles.
- Compare dimension-line placement when relevant.
- Produce feature-level scores and a total score.

### 7. Review Reporter

Produces human-readable evidence.

Responsibilities:

- Candidate contact sheets.
- Overlay images.
- Difference images.
- Feature-score tables.
- Pass/fail/needs-review flags.
- Notes field for human reviewer conclusions.

## What the harness should not do

- It should not become the production CAD kernel.
- It should not export manufacturing solids.
- It should not make final interpretation decisions automatically.
- It should not depend on OCR as a primary comparison method.
- It should not require a pixel-perfect clone of the Flash renderer before geometry can be evaluated.

## Recommended directory layout for an implementation

```text
rts-geometry-harness/
  inputs/
    parameters/
    assumptions/
    references/
    annotations/
  generated/
    candidates/
    overlays/
    reports/
  schemas/
  docs/
```

## Minimum viable harness run

A minimum useful run should be able to answer:

```text
Preset: BP Core Burner, A = 0.75 in
Assumptions: I external taper to bore opening, E from axis, G from shoulder face
Reference: 01-bp-core-burner-0.75in.png
Result: candidate render + overlay + feature score + reviewer notes
```
