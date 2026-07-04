# 03 — Assumption Toggle Catalog

The harness should make ambiguous interpretation choices explicit and testable. This catalog is the initial set of toggles.

## Fixed truths for this pass

The following should not be treated as open assumptions in the first harness pass because they have been provided as known truths:

```text
All rammers have straight open-bottom cylindrical bores.
I applies only to the first/longest rammer.
I forms the backside of the nozzle.
The I taper ends at the bore opening.
The shown groove is a real do-not-pass line.
A second practical change-rammers line exists but is not shown in original screenshots.
Displayed dimensions are intended finished tooling dimensions.
```

The harness can still include toggles around how these are drawn or represented, but not whether they are conceptually true.

## A. Spindle taper `E`

### Toggle: `angle_conventions.E`

Values to test:

```text
from_axis
from_perpendicular_to_axis
included_angle
```

Recommended first-pass candidates:

1. `from_axis` — diameter change over length uses `2*C*tan(E)`.
2. `from_perpendicular_to_axis` — alternate convention, likely poor fit but useful to falsify.
3. `included_angle` — use half angle for side profile, if checking whether the UI labels included taper.

### Toggle: `spindle.e_taper_sign`

Values:

```text
diameter_decreases_toward_tip
diameter_increases_toward_tip
```

Expected winner: `diameter_decreases_toward_tip`.

## B. Collar taper `G`

### Toggle: `angle_conventions.G`

Values to test:

```text
from_shoulder_face
from_axis
from_perpendicular_to_axis
```

Expected likely winner: `from_shoulder_face`, because the Flash profile formula behaves like a radial/shoulder-face angle convention.

### Toggle: `spindle.g_profile_mode`

Values:

```text
flash_formula_points
direct_conical_between_A_and_D
square_when_zero_else_flash_formula
```

Notes:

- `flash_formula_points` should reproduce the decompiled ActionScript profile directly.
- `direct_conical_between_A_and_D` is a sanity-check convention.
- `square_when_zero_else_flash_formula` should likely be the production/default interpretation.

### Toggle: `spindle.g_zero_mode`

Values:

```text
square_shoulder
zero_slope_taper
fallback_to_flash_formula
```

Expected winner: `square_shoulder`.

## C. First/longest rammer taper `I`

### Toggle: `angle_conventions.I`

Values to test:

```text
from_face
from_axis
included_angle
```

Because `I` forms the backside of the nozzle and the screenshots show an angled working-end region, `from_face` is a strong first candidate. Still, the harness should render alternatives to confirm.

### Toggle: `rammers.i_feature`

Values:

```text
external_backside_nozzle_taper
internal_chamfer_to_bore
combined_external_and_internal_marker
```

Expected winner based on current known truths: `external_backside_nozzle_taper`.

### Toggle: `rammers.i_applies_to`

Values:

```text
first_longest_rammer_only
solid_a_rammer_only
all_hollow_rammers
```

Known-truth value for this pass: `first_longest_rammer_only`.

Keep the other values only as falsification experiments when comparing older interpretation notes.

### Toggle: `rammers.i_taper_end`

Values:

```text
bore_opening
small_flat_before_bore_opening
centerline_apex
outer_edge_only
```

Known-truth value for this pass: `bore_opening`.

The important tested ambiguity is not the final conceptual rule, but whether the original Flash drawing visually leaves a tiny flat due to stroke width, rounding, or pixel aliasing.

### Toggle: `rammers.i_taper_has_flat_lip`

Values:

```text
false
true_with_fixed_lip
true_with_lip_ratio_to_A
```

Expected winner: `false`, because the taper is now known to end at the bore opening. However, a render variant with a tiny flat is useful to detect whether the screenshot shows a real flat or just rasterization.

### Toggle: `rammers.i_taper_start_rule`

Values:

```text
outer_diameter_at_working_face
intersects_outer_wall_by_angle
fixed_axial_length_from_working_face
derived_from_bore_diameter_and_angle
```

Recommended first-pass rule: `derived_from_bore_diameter_and_angle`.

Rationale: if the taper ends at the bore opening and forms the backside of the nozzle, then the taper endpoint is bore diameter at the working face/open end. The start is probably the intersection with the OD or working face boundary implied by angle `I`.

## D. Bore rendering and interpretation

### Toggle: `rammers.bore_model`

Fixed value for this pass:

```text
straight_open_bottom_cylindrical
```

### Toggle: `rammers.bore_visibility`

Values:

```text
hidden_dashed
hidden_dashed_with_open_bottom
solid_section_cut_for_debug
not_drawn
```

Expected Flash-like value: `hidden_dashed`.

Debug value: `solid_section_cut_for_debug` can help visually confirm that the generated bore coincides with the dashed rectangle.

### Toggle: `rammers.bore_bottom_style`

Values:

```text
flat_square
rounded_visual_only
drill_point_visual_only
```

The original screenshots look like square-ended dashed rectangles. For comparison, use `flat_square`.

## E. Groove / do-not-pass line

### Toggle: `rammers.show_no_pass_line`

Values:

```text
true
false
```

Known-truth value: `true`.

### Toggle: `rammers.no_pass_line_mode`

Values:

```text
drawn_mark_only
shallow_physical_groove
shoulder_step
```

For screenshot comparison, `drawn_mark_only` should be tested first. The line is physically meaningful as a do-not-pass mark, but that does not prove the rendered mark must be modeled as a groove in the side-view geometry.

### Toggle: `rammers.no_pass_line_position`

Values:

```text
ri_from_top
ri_from_striking_end
legacy_flash_position
```

Expected winner: `ri_from_top` or `legacy_flash_position`, depending on the drawing coordinate convention.

### Toggle: `rammers.show_second_change_line`

Values:

```text
false
true_reference_only
true_dashed_process_marker
```

Expected Flash-like value: `false`, because the practical second change-rammers line is not shown in the original screenshots.

## F. Drawing/rendering toggles

These are not geometry interpretations, but they affect visual comparison.

```text
rendering.include_dimensions
rendering.include_text_labels
rendering.include_helper_markers
rendering.flash_like_layout
rendering.stroke_width_px
rendering.hidden_dash_pattern
rendering.dimension_arrow_style
rendering.y_axis_direction
rendering.part_spacing_mode
rendering.round_display_values
```

Use these only after the actual geometry conventions are narrowed. Otherwise renderer differences can obscure geometry differences.
