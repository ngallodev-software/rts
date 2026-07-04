# Rocket Tool Sketcher Geometry Comparison Harness — First-Pass Design

This package is a lightweight, screenshot-driven test-harness design for evaluating ambiguous geometry conventions in the legacy Flash **Rocket Tool Sketcher** before locking the modern CAD model.

It is intentionally not a UI design and not a production CAD export design. The harness exists to answer one question repeatedly:

> Given one parameter set and one interpretation/assumption set, does the rendered candidate geometry visually agree with the original Flash screenshot?

## Package contents

```text
README.md

docs/
  01-harness-design.md
  02-data-structures.md
  03-assumption-toggle-catalog.md
  04-rendering-strategy.md
  05-comparison-and-scoring.md
  06-manual-validation-workflow.md
  07-automation-boundaries.md
  08-review-checklist.md

schemas/
  parameters.schema.json
  assumption-set.schema.json
  derived-geometry.schema.json
  reference-metadata.schema.json
  comparison-result.schema.json

examples/
  presets-0.75in.json
  assumption-matrix.json
  references.example.json
  manual-annotations.example.json
  run-plan.example.json

templates/
  review-report-template.md
  candidate-id-convention.md

references/
  README.md
```

## Intended workflow

1. Put the original preset screenshots in a local `references/presets/` folder.
2. Put helper screenshots in `references/helpers/`.
3. Load one preset parameter set from `examples/presets-0.75in.json` or equivalent.
4. Select one or more assumption sets from `examples/assumption-matrix.json`.
5. Generate simplified 2D side-view candidate renders.
6. Normalize each candidate against its reference screenshot using manually supplied anchors.
7. Score visual/geometric agreement.
8. Review a contact sheet and decide whether each ambiguous convention is confirmed, rejected, or still unresolved.

## Non-goals

- No modern app UI choices.
- No web framework choices.
- No production STEP/DXF/STL implementation details.
- No attempt to infer safety, performance, or use instructions for pyrotechnic devices.

The harness is only for geometry interpretation and drawing-convention validation.
