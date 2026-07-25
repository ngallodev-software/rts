# Export Verification Checklist

This checklist is a release gate. Run every applicable automated check and complete every applicable visual check whenever an exporter, geometry rule, unit conversion, annotation, or packaging path changes. A failed item blocks release.

## Release control

- [ ] Identify every affected component in `version-manifest.json` before editing.
- [ ] Bump only affected component versions using the manifest's Semantic Versioning policy.
- [ ] Add a README version-addendum entry stating what changed and what should improve.
- [ ] Generate the canonical `.75 in BP Core burner` regression set.
- [ ] Generate at least one metric set when units, dimensions, tolerances, or scaling changed.
- [ ] Run `python scripts/verify_exports.py <export-directory>` and retain `verification-report.json`.
- [ ] Compare all unchanged component versions and artifacts with the prior accepted release.

## Drawing-wide checks

- [ ] Every physical part appears exactly once in the combined set and once as an individual export.
- [ ] Titles, notes, dimensions, leaders, tables, and geometry remain inside their assigned part zone.
- [ ] No part zone overlaps or obscures any neighboring part zone.
- [ ] No leader or extension line crosses dimension text.
- [ ] Units, decimal precision, diameter symbols, and degree symbols match the selected drawing unit.
- [ ] Dimensions remain finished-tool dimensions and match the manifest.
- [ ] Hidden bores, centerlines, do-not-pass marks, and switch-rammer marks are present where required.
- [ ] No unexplained diagonal, duplicate, orphaned, or zero-length entities appear.

## DXF checks

- [ ] `ezdxf` audit reports zero errors and zero repairs for every generated DXF.
- [ ] `$INSUNITS` and dimension suffixes match inches or millimeters.
- [ ] Required layers exist and retain readable colors/linetypes.
- [ ] The combined annotated DXF passes the embedded `RTS_QA` part-zone separation check.
- [ ] Open the combined annotated DXF in Solid Edge and inspect at fit-to-window and close zoom.
- [ ] Import the clean R12 DXF into Fusion 360 and verify the tube I.D. measurement.
- [ ] Spot-check one spindle, the full-depth A rammer, and the shortest rammer.

## PDF checks

- [ ] Combined PDF is landscape letter and contains exactly four pages for the canonical set.
- [ ] Pages 1-3 show complete tools without clipping or distorted proportions.
- [ ] Page 4 notes and table have clear separation and no missing rows.
- [ ] PDF dimensions, notes, symbols, tolerances, and marks agree with the annotated DXF.
- [ ] Render every page to PNG and visually inspect at 100% scale.

## STEP checks

- [ ] Combined STEP contains one spindle/collar plus the expected number of separate rammers.
- [ ] Separate STEP count matches the physical-part count.
- [ ] Inch inputs import at the correct millimeter interchange scale (`.75 in = 19.05 mm`).
- [ ] Blind bores, working-end tapers, collar, and part spacing remain correct.

## STL checks

- [ ] Combined and separate STL counts match STEP.
- [ ] Meshes are nonempty, watertight where expected, and visually match STEP.
- [ ] STL is labeled as preview geometry rather than the authoritative machining model.

## OpenSCAD checks

- [ ] File opens and renders without errors in OpenSCAD.
- [ ] A-I inputs, units, part count, clearances, and mark locations match the manifest.
- [ ] Each physical part remains a separate selectable module and combined layout item.

## Web and ZIP checks

- [ ] Web production build succeeds with no browser console errors.
- [ ] Unit switching converts dimensions, tolerances, clearances, and finish units together.
- [ ] Every export button downloads the advertised artifact ZIP.
- [ ] Every ZIP contains `version-manifest.json` and only the expected artifact family.
- [ ] Generated `tooling-set.json` embeds the same component versions as the root manifest.

## Release decision

- [ ] Record any accepted limitation in the README addendum before release.
- [ ] Do not release if a changed artifact was not visually inspected in at least one target CAD/viewer application.
- [ ] Do not release if an unchanged exporter regressed from the prior accepted output.
