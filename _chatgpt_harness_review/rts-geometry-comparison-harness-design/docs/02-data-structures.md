# 02 — Data Structures

This file defines the minimal data records needed for the comparison harness. The JSON schemas in `schemas/` are stricter machine-readable versions of the same concepts.

## 1. Input parameter set

A parameter set is the raw design input.

```json
{
  "id": "bp-core-burner-075in",
  "name": "BP Core Burner 0.75 in",
  "preset_key": "bp_core_burner",
  "units": "in",
  "source": "original_flash_preset",
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
  },
  "notes": [
    "Preset values are ratio-driven from A."
  ]
}
```

### Field notes

| Field | Meaning |
|---|---|
| `A` | Tube I.D. |
| `B` | Tube length |
| `C` | Spindle length |
| `D` | Spindle width/root width |
| `E` | Spindle taper angle |
| `F` | Collar height |
| `G` | Collar taper angle |
| `H` | Number of rammers |
| `I` | A/first/longest rammer taper angle |

## 2. Derived geometry

Derived geometry is not merely raw drawing primitives. It should preserve part and feature semantics so comparisons can be made feature-by-feature.

```json
{
  "parameter_set_id": "bp-core-burner-075in",
  "assumption_set_id": "flash-like-baseline-v01",
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
      "part_id": "rammer_01_a_rammer",
      "part_type": "rammer",
      "role": "first_longest_hollow_rammer_with_nozzle_back_taper",
      "features": []
    }
  ],
  "dimensions": [],
  "warnings": []
}
```

### Feature record

Every generated line, polyline, arc, marker, hidden region, or dimension should have a feature record.

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

Recommended `draw_role` values:

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

Recommended `manufacturing_role` values:

```text
external_geometry
negative_geometry
reference_only
process_indicator
dimension_annotation
not_manufacturing_geometry
```

## 3. Assumption set

An assumption set defines ambiguous geometry conventions.

```json
{
  "id": "flash-like-baseline-v01",
  "label": "Flash-like baseline v01",
  "angle_conventions": {
    "E": "from_axis",
    "G": "from_shoulder_face",
    "I": "from_face"
  },
  "spindle": {
    "e_taper_sign": "diameter_decreases_toward_tip",
    "g_zero_mode": "square_shoulder",
    "g_profile_mode": "flash_formula_points"
  },
  "rammers": {
    "bore_model": "straight_open_bottom_cylindrical",
    "bore_visibility": "hidden_dashed",
    "i_applies_to": "first_longest_rammer_only",
    "i_feature": "external_backside_nozzle_taper",
    "i_taper_end": "bore_opening",
    "i_taper_has_flat_lip": false,
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

## 4. Reference screenshot metadata

Screenshot metadata should not be inferred on every run. Store it once and then refine it.

```json
{
  "id": "ref-bp-core-burner-075in",
  "file": "references/presets/01-bp-core-burner-0.75in.png",
  "preset_key": "bp_core_burner",
  "units": "in",
  "image_size_px": { "width": 1177, "height": 810 },
  "regions": {
    "spindle": { "x": 0, "y": 0, "w": 420, "h": 360 },
    "rammer_01": { "x": 0, "y": 340, "w": 360, "h": 430 },
    "rammer_02": { "x": 380, "y": 0, "w": 420, "h": 360 }
  },
  "anchors": [
    {
      "name": "spindle_axis_start",
      "image_px": [100, 170],
      "model_ref": "spindle.axis.root"
    }
  ],
  "annotations_file": "annotations/bp-core-burner-075in.annotations.json",
  "notes": []
}
```

## 5. Comparison result

```json
{
  "candidate_id": "bp-core-burner-075in__flash-like-baseline-v01",
  "reference_id": "ref-bp-core-burner-075in",
  "scores": {
    "total": 0.87,
    "outer_profile": 0.93,
    "hidden_bores": 0.88,
    "i_taper": 0.81,
    "g_collar": 0.92,
    "dimensions_layout": 0.72
  },
  "decision": "needs_human_review",
  "flags": [
    "I taper endpoint differs by more than threshold",
    "dimension text placement ignored in total score"
  ],
  "artifacts": {
    "candidate_render": "generated/candidates/...png",
    "overlay": "generated/overlays/...png",
    "difference": "generated/overlays/...diff.png"
  },
  "reviewer_notes": "Candidate matches spindle and bores. I taper needs focused review."
}
```
