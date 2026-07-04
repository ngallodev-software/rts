# Rocket Tool Sketcher Modern

A browser-based rebuild of the original `rockettoolsketcher.swf`, with a shared geometry model that now also drives CAD export generation.

## Current scope

- Supports a `Custom` mode with editable A-I dimensions.
- Includes the baked-in preset families extracted from the Flash app.
- Uses one shared spindle and rammer geometry model for the browser preview and export work.
- Includes a first-pass screenshot comparison harness for validating ambiguous angle conventions.
- Generates manufacturing exports from Python:
  - combined clean `DXF`
  - combined annotated `DXF`
  - separate clean `DXF` per part
  - separate annotated `DXF` per part
  - combined `STEP`
  - separate `STEP` per part
  - combined `STL`
  - separate `STL` per part
  - generated parametric `OpenSCAD`
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

- The original SWF export, decompiled ActionScript, screenshots, and the user-supplied manufacturing interpretation notes are all being used to converge on the final geometry rules.
- This is a clean web rebuild, not a Flash wrapper.
- The export backend currently lives in [`rts_export`](C:/Users/natha/source/repos/rts/rts_export).
