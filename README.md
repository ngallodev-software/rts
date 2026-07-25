# Rocket Tool Sketcher Modern

A browser-based rebuild of the original `rockettoolsketcher.swf`, with a shared geometry model that now also drives CAD export generation.

## Current scope

- Supports a `Custom` mode with editable A-I dimensions.
- Includes the baked-in preset g dimensions for some common device types matching the original flash app.
- Uses one shared spindle and rammer geometry model for the browser preview and export work.
- Generates manufacturing exports from Python:
  - combined clean as well as separate, per-part `DXF` files and / or annotated `DXF` files
  - combined and individual `STEP` and `STL` 3D models
  - generated parametric `OpenSCAD` script
  - JSON manifest of the exact derived dimensions

## Run the app

```bash
npm install
npm run dev
```

## Build the app

```bash
npm run build
```

## Generate CAD exports

Example using a baked-in preset:

```bash
python -m rts_export.cli --preset bp-core-burner --tube-id 0.75 --output exports/bp-core-burner-075
```

List presets:

```bash
python -m rts_export.cli --list-presets
```

Example using fully custom A-I values:

```bash
python -m rts_export.cli --preset custom --output exports/custom ^
  --a 0.75 --b 6 --c 2.5 --d 0.375 --e 1.5 --f 0.413 --g 30 --h 3 --i 0
```

## Export notes

- The baseline export assumption currently matches the working interpretation used in the refactored geometry model:
  - `E` from axis
  - `G` from shoulder face
  - `I` from face
  - do-not-pass groove modeled as a shallow V-groove
- The generated DXFs use separate layers for visible profiles, hidden bores, centerlines, dimensions, and text.
- The default `tooling-set.dxf` is the import-friendly geometry sheet. `tooling-set-annotated.dxf` carries the dimensions and titles.
- `STEP`, `STL`, and generated `OpenSCAD` geometry are written with CAD-interchange scaling in mind. If inputs are inches, the exported 3D geometry is scaled to millimeters.
- The OpenSCAD output is intended to stay editable by changing the input values at the top of the file.

## Project notes

## Export verification

The release gate is [`docs/export-verification-checklist.md`] Generate a canonical export and run:

```bash
python scripts/verify_exports.py exports/core-burner-075-layout-v110
```

The verifier audits every DXF, checks embedded annotation-zone separation, validates component versions and artifact counts, validates the four-page PDF, and renders its pages for visual review. Automated checks supplement, rather than replace, the Solid Edge/Fusion 360 and rendered-page inspections in the checklist.

## Version addendum

Component versions are maintained in [`version-manifest.json`], embedded in `tooling-set.json`, copied into every export directory, and included in every download ZIP.

### Release 1.0.0 - version baseline

- Assigned independent `1.0.0` versions to the web UI, export API, geometry model, clean DXF, annotated DXF, annotated PDF, STEP, STL, OpenSCAD, tooling manifest, and verification harness.
- This release records the accepted functional baseline; it does not claim that earlier prototypes had equivalent release quality.

### Release 1.1.0 - annotated DXF zone isolation

- Changed only the combined annotated-DXF layout behavior; `dxf_annotated` is now `1.1.0`.
- Replaced fixed part spacing with measured annotation envelopes for the spindle, each rammer, and the overview/table.
- Intended improvement: a part's title, notes, dimensions, leaders, and geometry cannot overlap or obscure the neighboring part's zone when note content grows.
- Added invisible `RTS_QA` zone metadata so the saved DXF can be checked independently by the verifier.
- Added the permanent export checklist and automated verifier. Geometry formulas and clean DXF, PDF, STEP, STL, and OpenSCAD generation were not intentionally changed in this release.
