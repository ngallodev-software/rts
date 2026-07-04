from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable
import math

import cadquery as cq
import ezdxf
from cadquery import exporters as cq_exporters
from ezdxf import bbox
from ezdxf import zoom

from .model import (
    BASELINE_ASSUMPTION,
    MM_PER_INCH,
    AssumptionSet,
    ExportBundle,
    RammerModel,
    SpindleModel,
    ToolModel,
    ToolParams,
    build_tool_model,
)
from .presets import PresetDefinition


LAYER_PROFILE = "PROFILE"
LAYER_HIDDEN = "HIDDEN"
LAYER_CENTER = "CENTER"
LAYER_DIM = "DIM"
LAYER_TEXT = "TEXT"
LAYER_TITLE = "TITLE"
LAYER_MARKS = "MARKS"
LAYER_NOTES = "NOTES"
LAYER_TABLE = "TABLE"


def format_value(value: float) -> str:
    text = f"{value:.4f}"
    return text.rstrip("0").rstrip(".")


def slugify(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _setup_layers(doc: ezdxf.EzDxfDocument) -> None:
    layers = doc.layers
    if LAYER_PROFILE not in layers:
        layers.add(LAYER_PROFILE, color=7)
    if LAYER_HIDDEN not in layers:
        layers.add(LAYER_HIDDEN, color=8, linetype="HIDDEN")
    if LAYER_CENTER not in layers:
        layers.add(LAYER_CENTER, color=3, linetype="CENTER")
    if LAYER_DIM not in layers:
        layers.add(LAYER_DIM, color=7)
    if LAYER_TEXT not in layers:
        layers.add(LAYER_TEXT, color=7)
    if LAYER_TITLE not in layers:
        layers.add(LAYER_TITLE, color=7)
    if LAYER_MARKS not in layers:
        layers.add(LAYER_MARKS, color=7)
    if LAYER_NOTES not in layers:
        layers.add(LAYER_NOTES, color=7)
    if LAYER_TABLE not in layers:
        layers.add(LAYER_TABLE, color=7)


def _new_doc(unit: str, annotated: bool, dxf_version: str = "R2010") -> ezdxf.EzDxfDocument:
    doc = ezdxf.new(dxf_version, setup=annotated)
    _setup_layers(doc)
    if dxf_version != "R12":
        doc.header["$INSUNITS"] = 1 if unit == "in" else 4
        doc.header["$MEASUREMENT"] = 0 if unit == "in" else 1
        doc.header["$LTSCALE"] = 1.0
        doc.header["$DIMLFAC"] = 1.0
        doc.header["$DIMDEC"] = 3
        doc.header["$DIMZIN"] = 8
        _normalize_dimstyles(doc)
    return doc


def _normalize_dimstyles(doc: ezdxf.EzDxfDocument) -> None:
    for name in ("EZDXF", "EZ_CURVED"):
        if name in doc.dimstyles:
            style = doc.dimstyles.get(name)
            style.dxf.dimlfac = 1.0
            style.dxf.dimdec = 3
            style.dxf.dimzin = 8
            style.dxf.dimdsep = ord(".")
            style.dxf.dimasz = 0.175
            style.dxf.dimtxt = 0.1


def _translate_points(points: Iterable[tuple[float, float]], dx: float, dy: float) -> list[tuple[float, float]]:
    return [(x + dx, y + dy) for x, y in points]


def _add_profile(msp: ezdxf.layouts.Modelspace, points: list[tuple[float, float]]) -> None:
    msp.add_lwpolyline(points, dxfattribs={"layer": LAYER_PROFILE, "closed": True})


def _add_profile_lines(msp: ezdxf.layouts.Modelspace, points: list[tuple[float, float]]) -> None:
    for start, end in zip(points, points[1:] + [points[0]]):
        msp.add_line(start, end, dxfattribs={"layer": LAYER_PROFILE})


def _add_centerline(msp: ezdxf.layouts.Modelspace, x: float, top: float, bottom: float) -> None:
    msp.add_line((x, top), (x, bottom), dxfattribs={"layer": LAYER_CENTER, "linetype": "CENTER"})


def _render_linear_dim(
    msp: ezdxf.layouts.Modelspace,
    p1: tuple[float, float],
    p2: tuple[float, float],
    location: tuple[float, float],
    angle: float = 0.0,
) -> None:
    dim = msp.add_linear_dim(
        base=location,
        p1=p1,
        p2=p2,
        location=location,
        angle=angle,
        dxfattribs={"layer": LAYER_DIM},
        override={"dimtad": 1, "dimtxt": 0.1, "dimlfac": 1.0, "dimdec": 3, "dimzin": 8},
    )
    dim.render()


def _render_angular_dim(
    msp: ezdxf.layouts.Modelspace,
    line1: tuple[tuple[float, float], tuple[float, float]],
    line2: tuple[tuple[float, float], tuple[float, float]],
    location: tuple[float, float],
) -> None:
    dim = msp.add_angular_dim_2l(
        base=location,
        line1=line1,
        line2=line2,
        location=location,
        dxfattribs={"layer": LAYER_DIM},
        override={"dimtad": 1, "dimtxt": 0.1, "dimlfac": 1.0, "dimdec": 3, "dimzin": 8},
    )
    dim.render()


def _add_title(msp: ezdxf.layouts.Modelspace, text: str, x: float, y: float) -> None:
    msp.add_text(text, dxfattribs={"height": 0.08, "layer": LAYER_TITLE}).set_placement((x, y))


def _add_note_line(msp: ezdxf.layouts.Modelspace, text: str, x: float, y: float, height: float = 0.075) -> None:
    msp.add_text(text, dxfattribs={"height": height, "layer": LAYER_NOTES}).set_placement((x, y))


def _add_multiline_notes(
    msp: ezdxf.layouts.Modelspace,
    lines: list[str],
    x: float,
    y: float,
    height: float = 0.075,
    line_spacing: float = 0.11,
) -> None:
    cursor = y
    for line in lines:
        _add_note_line(msp, line, x, cursor, height)
        cursor -= line_spacing


def _format_diameter(value: float) -> str:
    return f"%%c{value:.3f}"


def _format_length(value: float) -> str:
    return f"{value:.3f}"


def _spindle_taper_per_side(spindle: SpindleModel) -> float:
    if spindle.spindle_length <= 0:
        return 0.0
    return math.degrees(math.atan(((spindle.root_diameter - spindle.tip_diameter) / 2) / spindle.spindle_length))


def _collar_taper_from_shoulder_face(spindle: SpindleModel) -> float:
    radial = (spindle.tube_diameter - spindle.root_diameter) / 2
    if spindle.collar_rise <= 0 or radial <= 0:
        return 0.0
    return math.degrees(math.atan(spindle.collar_rise / radial))


def _spindle_outline_points(spindle: SpindleModel) -> list[tuple[float, float]]:
    straight_height = max(spindle.collar_height - spindle.collar_rise, 0.0)
    return [
        (-spindle.tip_diameter / 2, 0.0),
        (spindle.tip_diameter / 2, 0.0),
        (spindle.root_diameter / 2, spindle.spindle_length),
        (spindle.tube_diameter / 2, spindle.total_length - straight_height),
        (spindle.tube_diameter / 2, spindle.total_length),
        (-spindle.tube_diameter / 2, spindle.total_length),
        (-spindle.tube_diameter / 2, spindle.total_length - straight_height),
        (-spindle.root_diameter / 2, spindle.spindle_length),
    ]


def _rammer_outline_points(rammer: RammerModel) -> list[tuple[float, float]]:
    half_outer = rammer.outer_diameter / 2
    if rammer.has_taper and rammer.taper_height > 0:
        return [
            (-rammer.bore_diameter / 2, 0.0),
            (rammer.bore_diameter / 2, 0.0),
            (half_outer, rammer.taper_height),
            (half_outer, rammer.overall_length),
            (-half_outer, rammer.overall_length),
            (-half_outer, rammer.taper_height),
        ]
    return [
        (-half_outer, 0.0),
        (half_outer, 0.0),
        (half_outer, rammer.overall_length),
        (-half_outer, rammer.overall_length),
    ]


def _length_scale(unit: str) -> float:
    return MM_PER_INCH if unit == "in" else 1.0


def _scale_points(points: Iterable[tuple[float, float]], factor: float) -> list[tuple[float, float]]:
    return [(x * factor, y * factor) for x, y in points]


def _scaled_spindle(spindle: SpindleModel, factor: float) -> SpindleModel:
    return SpindleModel(
        tube_diameter=spindle.tube_diameter * factor,
        collar_height=spindle.collar_height * factor,
        spindle_length=spindle.spindle_length * factor,
        root_diameter=spindle.root_diameter * factor,
        tip_diameter=spindle.tip_diameter * factor,
        total_length=spindle.total_length * factor,
        collar_rise=spindle.collar_rise * factor,
        points=_scale_points(spindle.points, factor),
    )


def _scaled_rammer(rammer: RammerModel, factor: float) -> RammerModel:
    return RammerModel(
        key=rammer.key,
        label=rammer.label,
        role=rammer.role,
        overall_length=rammer.overall_length * factor,
        outer_diameter=rammer.outer_diameter * factor,
        head_length=rammer.head_length * factor,
        groove_from_top=rammer.groove_from_top * factor,
        bore_depth=rammer.bore_depth * factor,
        bore_diameter=rammer.bore_diameter * factor,
        nose_angle=rammer.nose_angle,
        taper_height=rammer.taper_height * factor,
        has_taper=rammer.has_taper,
        points=_scale_points(rammer.points, factor),
    )


def _update_header_extents(doc: ezdxf.EzDxfDocument, msp: ezdxf.layouts.Modelspace) -> None:
    extents = bbox.extents(msp)
    doc.header["$EXTMIN"] = extents.extmin
    doc.header["$EXTMAX"] = extents.extmax


def _part_bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), max(xs), min(ys), max(ys)


def _draw_hidden_bore(
    msp: ezdxf.layouts.Modelspace,
    bore_diameter: float,
    bore_depth: float,
    overall_length: float,
    dx: float,
    dy: float,
) -> None:
    if bore_diameter <= 0 or bore_depth <= 0:
        return
    left = dx - bore_diameter / 2
    right = dx + bore_diameter / 2
    top = dy - (overall_length - bore_depth)
    bottom = dy - overall_length
    attribs = {"layer": LAYER_HIDDEN, "linetype": "HIDDEN"}
    msp.add_line((left, top), (left, bottom), dxfattribs=attribs)
    msp.add_line((right, top), (right, bottom), dxfattribs=attribs)
    msp.add_line((left, top), (right, top), dxfattribs=attribs)


def _draw_spindle(
    msp: ezdxf.layouts.Modelspace,
    spindle: SpindleModel,
    origin_x: float,
    origin_y: float,
    title: str,
    include_dimensions: bool,
    include_titles: bool,
    compatibility_mode: bool,
) -> None:
    raw_points = _spindle_outline_points(spindle)
    points = [(origin_x + x, origin_y - y) for x, y in raw_points]
    if compatibility_mode:
        _add_profile_lines(msp, points)
    else:
        _add_profile(msp, points)
    min_x, max_x, min_y, max_y = _part_bounds(points)
    if not compatibility_mode:
        _add_centerline(msp, origin_x, max_y + 0.35, min_y - 0.35)
    if include_titles:
        _add_title(msp, title, min_x, max_y + 0.7)

    if not include_dimensions:
        return

    _render_linear_dim(msp, (min_x, max_y), (max_x, max_y), (origin_x, max_y + 0.45), angle=0)
    _render_linear_dim(msp, (max_x, max_y), (max_x, min_y), (max_x + 0.45, (max_y + min_y) / 2), angle=90)
    _render_linear_dim(
        msp,
        (origin_x + spindle.root_diameter / 2, origin_y - spindle.collar_height),
        (origin_x + spindle.tip_diameter / 2, origin_y - spindle.total_length),
        (origin_x + spindle.root_diameter / 2 + 0.45, origin_y - spindle.total_length / 2),
        angle=90,
    )
    _render_linear_dim(
        msp,
        (origin_x + spindle.root_diameter / 2, origin_y - spindle.collar_height),
        (origin_x - spindle.root_diameter / 2, origin_y - spindle.collar_height),
        (origin_x, origin_y - spindle.collar_height - 0.4),
        angle=0,
    )
    _render_linear_dim(
        msp,
        (origin_x + spindle.tip_diameter / 2, origin_y - spindle.total_length),
        (origin_x - spindle.tip_diameter / 2, origin_y - spindle.total_length),
        (origin_x, origin_y - spindle.total_length - 0.45),
        angle=0,
    )

    notes = [
        "PART 1 - SPINDLE / CORE FORMER",
        f"COLLAR OD {_format_diameter(spindle.tube_diameter)}",
        f"COLLAR HEIGHT {_format_length(spindle.collar_height)}",
        f"ROOT OD {_format_diameter(spindle.root_diameter)}",
        f"TIP OD {_format_diameter(spindle.tip_diameter)}",
        f"SPINDLE LENGTH {_format_length(spindle.spindle_length)}",
        f"OVERALL LENGTH {_format_length(spindle.total_length)}",
        f"SPINDLE TAPER: {_format_length(_spindle_taper_per_side(spindle))} DEG PER SIDE",
        f"COLLAR TAPER: {_format_length(_collar_taper_from_shoulder_face(spindle))} DEG FROM SHOULDER FACE",
        "SPINDLE SHOWN COLLAR END DOWN / WORKING END UP",
    ]
    _add_multiline_notes(msp, notes, max_x + 0.5, max_y - 0.1)


def _draw_rammer(
    msp: ezdxf.layouts.Modelspace,
    rammer: RammerModel,
    origin_x: float,
    origin_y: float,
    title: str,
    include_dimensions: bool,
    include_titles: bool,
    compatibility_mode: bool,
) -> None:
    raw_points = _rammer_outline_points(rammer)
    points = [(origin_x + x, origin_y - y) for x, y in raw_points]
    if compatibility_mode:
        _add_profile_lines(msp, points)
    else:
        _add_profile(msp, points)
    _draw_hidden_bore(msp, rammer.bore_diameter, rammer.bore_depth, rammer.overall_length, origin_x, origin_y)
    min_x, max_x, min_y, max_y = _part_bounds(points)
    if not compatibility_mode:
        _add_centerline(msp, origin_x, max_y + 0.35, min_y - 0.35)
        mark_y = origin_y - rammer.groove_from_top
        msp.add_line(
            (origin_x - rammer.outer_diameter / 2, mark_y),
            (origin_x + rammer.outer_diameter / 2, mark_y),
            dxfattribs={"layer": LAYER_MARKS},
        )
    if include_titles:
        _add_title(msp, title, min_x, max_y + 0.7)

    if not include_dimensions:
        return

    _render_linear_dim(msp, (min_x, max_y), (max_x, max_y), (origin_x, max_y + 0.45), angle=0)
    _render_linear_dim(msp, (max_x, max_y), (max_x, min_y), (max_x + 0.45, (max_y + min_y) / 2), angle=90)
    _render_linear_dim(
        msp,
        (origin_x + rammer.outer_diameter / 2, origin_y),
        (origin_x + rammer.outer_diameter / 2, origin_y - rammer.head_length),
        (origin_x + rammer.outer_diameter / 2 + 0.6, origin_y - rammer.head_length / 2),
        angle=90,
    )
    _render_linear_dim(
        msp,
        (origin_x + rammer.outer_diameter / 2, origin_y),
        (origin_x + rammer.outer_diameter / 2, origin_y - rammer.groove_from_top),
        (origin_x - rammer.outer_diameter / 2 - 0.6, origin_y - rammer.groove_from_top / 2),
        angle=90,
    )

    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        _render_linear_dim(
            msp,
            (origin_x - rammer.bore_diameter / 2, origin_y - rammer.overall_length),
            (origin_x + rammer.bore_diameter / 2, origin_y - rammer.overall_length),
            (origin_x, origin_y - rammer.overall_length - 0.45),
            angle=0,
        )
        _render_linear_dim(
            msp,
            (origin_x + rammer.bore_diameter / 2, origin_y - rammer.overall_length),
            (origin_x + rammer.bore_diameter / 2, origin_y - (rammer.overall_length - rammer.bore_depth)),
            (origin_x + rammer.bore_diameter / 2 + 0.55, origin_y - (rammer.overall_length - rammer.bore_depth / 2)),
            angle=90,
        )

    notes = [
        f"OD {_format_diameter(rammer.outer_diameter)}",
        f"OAL {_format_length(rammer.overall_length)}",
        f"DO-NOT-PASS MARK {_format_length(rammer.groove_from_top)} FROM TOP FACE",
        "RAMMER SHOWN WORKING END DOWN",
    ]
    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        notes.extend(
            [
                f"BORE {_format_diameter(rammer.bore_diameter)} x {_format_length(rammer.bore_depth)} DEEP",
                "STRAIGHT CYLINDRICAL BORE OPEN FROM WORKING END",
            ]
        )
    if rammer.has_taper and rammer.taper_height > 0:
        notes.extend(
            [
                f"{_format_length(rammer.nose_angle)} DEG BACKSIDE NOZZLE TAPER",
                f"TAPER TO {_format_diameter(rammer.bore_diameter)} BORE OPENING",
                "NO FLAT LAND AT BORE OPENING",
            ]
        )
    _add_multiline_notes(msp, [f"PART - {rammer.label.upper()}"] + notes, max_x + 0.45, max_y - 0.1)


def _build_spindle_solid(spindle: SpindleModel) -> cq.Workplane:
    segments: list[cq.Workplane] = []
    straight_height = max(spindle.collar_height - spindle.collar_rise, 0.0)
    if straight_height > 0:
        segments.append(cq.Workplane("XY").circle(spindle.tube_diameter / 2).extrude(straight_height))
    if spindle.collar_rise > 0:
        collar = (
            cq.Workplane("XY")
            .workplane(offset=straight_height)
            .circle(spindle.tube_diameter / 2)
            .workplane(offset=spindle.collar_rise)
            .circle(spindle.root_diameter / 2)
            .loft(combine=True)
        )
        segments.append(collar)
    shaft = (
        cq.Workplane("XY")
        .workplane(offset=spindle.collar_height)
        .circle(max(spindle.root_diameter / 2, 0.0001))
        .workplane(offset=spindle.spindle_length)
        .circle(max(spindle.tip_diameter / 2, 0.0001))
        .loft(combine=True)
    )
    segments.append(shaft)
    result = segments[0]
    for segment in segments[1:]:
        result = result.union(segment)
    return result


def _cut_v_groove(body: cq.Workplane, outer_diameter: float, groove_z: float, groove_depth: float) -> cq.Workplane:
    half = outer_diameter / 2
    notch = (
        cq.Workplane("XZ")
        .moveTo(half, groove_z - groove_depth)
        .lineTo(half - groove_depth, groove_z)
        .lineTo(half, groove_z + groove_depth)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    return body.cut(notch)


def _build_rammer_solid(rammer: RammerModel, assumption: AssumptionSet) -> cq.Workplane:
    body_length = rammer.overall_length - rammer.taper_height
    body = cq.Workplane("XY").circle(rammer.outer_diameter / 2).extrude(max(body_length, 0.0001))
    if rammer.has_taper and rammer.taper_height > 0:
        taper = (
            cq.Workplane("XY")
            .workplane(offset=body_length)
            .circle(rammer.outer_diameter / 2)
            .workplane(offset=rammer.taper_height)
            .circle(max(rammer.bore_diameter / 2, 0.0001))
            .loft(combine=True)
        )
        body = body.union(taper)
    elif rammer.taper_height <= 0 and rammer.overall_length > body_length:
        body = body.union(
            cq.Workplane("XY").workplane(offset=body_length).circle(rammer.outer_diameter / 2).extrude(rammer.overall_length - body_length)
        )

    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        bore = (
            cq.Workplane("XY")
            .workplane(offset=rammer.overall_length - rammer.bore_depth)
            .circle(rammer.bore_diameter / 2)
            .extrude(rammer.bore_depth)
        )
        body = body.cut(bore)

    if assumption.draw_physical_groove and assumption.groove_mode == "v-groove":
        groove_depth = max(rammer.outer_diameter * 0.03, 0.01)
        body = _cut_v_groove(body, rammer.outer_diameter, rammer.groove_from_top, groove_depth)

    return body


def _compound_layout(parts: list[tuple[str, cq.Workplane]], spacing: float) -> cq.Workplane:
    translated = []
    offset = 0.0
    for _, part in parts:
        bbox = part.val().BoundingBox()
        translated.append(part.translate((offset - bbox.xmin, 0, 0)))
        offset += (bbox.xlen or 0.0) + spacing
    result = translated[0]
    for part in translated[1:]:
        result = result.union(part)
    return result


def _write_step(path: Path, solid: cq.Workplane) -> None:
    cq_exporters.export(solid, str(path))


def _write_stl(path: Path, solid: cq.Workplane) -> None:
    cq_exporters.export(solid, str(path), tolerance=0.001, angularTolerance=0.1)


def _openscad_header(params: ToolParams, preset: PresetDefinition | None, assumption: AssumptionSet, unit: str) -> str:
    source = preset.key if preset else "custom"
    return "\n".join(
        [
            "// Generated by RTS exporter",
            f'unit = "{unit}";',
            f'preset = "{source}";',
            f'assumption = "{assumption.key}";',
            f"a = {format_value(params.a)};",
            f"b = {format_value(params.b)};",
            f"c = {format_value(params.c)};",
            f"d = {format_value(params.d)};",
            f"e = {format_value(params.e)};",
            f"f = {format_value(params.f)};",
            f"g = {format_value(params.g)};",
            f"h = {int(params.h)};",
            f"i = {format_value(params.i)};",
            "",
            f"unit_scale = {format_value(_length_scale(unit))};",
            "head_ratio = 1.5;",
            "head_length = a * head_ratio;",
            "",
        ]
    )


def _openscad_body(model: ToolModel) -> str:
    spindle = model.spindle
    module_blocks: list[str] = []
    placement_blocks: list[str] = []

    module_blocks.append(
        "\n".join(
            [
                "module groove_cut(outer_radius, groove_z, groove_depth) {",
                "  rotate_extrude($fn=128)",
                "    polygon(points=[",
                "      [outer_radius, groove_z - groove_depth],",
                "      [outer_radius - groove_depth, groove_z],",
                "      [outer_radius, groove_z + groove_depth]",
                "    ]);",
                "}",
            ]
        )
    )

    for index, rammer in enumerate(model.rammers):
        module_name = rammer.key.replace("-", "_")
        taper_block = ""
        if rammer.has_taper and rammer.taper_height > 0:
            taper_block = (
                f"  translate([0, 0, {format_value(rammer.overall_length - rammer.taper_height)} * unit_scale])\n"
                f"    cylinder(h={format_value(rammer.taper_height)} * unit_scale, r1={format_value(rammer.outer_diameter / 2)} * unit_scale, "
                f"r2={format_value(rammer.bore_diameter / 2)} * unit_scale, $fn=128);\n"
            )
        bore_block = ""
        if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
            bore_block = (
                f"    translate([0, 0, {format_value(rammer.overall_length - rammer.bore_depth)} * unit_scale])\n"
                f"      cylinder(h={format_value(rammer.bore_depth + 0.01)} * unit_scale, r={format_value(rammer.bore_diameter / 2)} * unit_scale, $fn=128);\n"
            )
        groove_block = ""
        if model.assumption.draw_physical_groove and model.assumption.groove_mode == "v-groove":
            groove_depth = max(rammer.outer_diameter * 0.03, 0.01)
            groove_block = (
                f"    groove_cut({format_value(rammer.outer_diameter / 2)} * unit_scale, {format_value(rammer.groove_from_top)} * unit_scale, {format_value(groove_depth)} * unit_scale);\n"
            )
        module_blocks.append(
            "\n".join(
                [
                    f"module {module_name}() {{",
                    "  difference() {",
                    "    union() {",
                    f"      cylinder(h={format_value(rammer.overall_length - rammer.taper_height)} * unit_scale, r={format_value(rammer.outer_diameter / 2)} * unit_scale, $fn=128);",
                    taper_block.rstrip(),
                    "    }",
                    bore_block.rstrip(),
                    groove_block.rstrip(),
                    "  }",
                    "}",
                ]
            ).replace("\n\n", "\n")
        )
        placement_blocks.append(
            f"translate([{format_value((index + 1) * (model.params.a * 1.8))} * unit_scale, 0, 0]) {module_name}();"
        )

    spindle_block = "\n".join(
        [
            "module spindle() {",
            "  union() {",
            f"    cylinder(h={format_value(max(spindle.collar_height - spindle.collar_rise, 0.0))} * unit_scale, r={format_value(spindle.tube_diameter / 2)} * unit_scale, $fn=128);",
            f"    translate([0, 0, {format_value(max(spindle.collar_height - spindle.collar_rise, 0.0))} * unit_scale])",
            f"      cylinder(h={format_value(spindle.collar_rise)} * unit_scale, r1={format_value(spindle.tube_diameter / 2)} * unit_scale, r2={format_value(spindle.root_diameter / 2)} * unit_scale, $fn=128);",
            f"    translate([0, 0, {format_value(spindle.collar_height)} * unit_scale])",
            f"      cylinder(h={format_value(spindle.spindle_length)} * unit_scale, r1={format_value(spindle.root_diameter / 2)} * unit_scale, r2={format_value(spindle.tip_diameter / 2)} * unit_scale, $fn=128);",
            "  }",
            "}",
        ]
    )
    module_blocks.append(spindle_block)
    placement_blocks.insert(0, "spindle();")
    return "\n\n".join(module_blocks + placement_blocks)


def _write_openscad(path: Path, model: ToolModel, preset: PresetDefinition | None, assumption: AssumptionSet, unit: str) -> None:
    text = _openscad_header(model.params, preset, assumption, unit) + _openscad_body(model)
    path.write_text(text, encoding="utf-8")


def _draw_part_document(path: Path, unit: str, annotated: bool, draw_callback, dxf_version: str = "R2010") -> None:
    doc = _new_doc(unit, annotated, dxf_version=dxf_version)
    msp = doc.modelspace()
    draw_callback(msp)
    if annotated and dxf_version != "R12":
        _normalize_dimstyles(doc)
    if annotated and dxf_version != "R12":
        _normalize_dimstyles(doc)
    zoom.extents(msp, factor=1.05)
    _update_header_extents(doc, msp)
    doc.saveas(path)


def _write_separate_dxf(
    output_dir: Path,
    model: ToolModel,
    preset_label: str,
    unit: str,
    include_dimensions: bool,
    dxf_version: str = "R2010",
    suffix_override: str | None = None,
) -> list[str]:
    written: list[str] = []
    suffix = suffix_override if suffix_override is not None else ("-annotated" if include_dimensions else "")
    compatibility_mode = (not include_dimensions) or dxf_version == "R12"
    include_titles = include_dimensions

    spindle_path = output_dir / f"spindle{suffix}.dxf"
    _draw_part_document(
        spindle_path,
        unit,
        include_dimensions,
        lambda msp: _draw_spindle(
            msp,
            model.spindle,
            0.0,
            0.0,
            f"{preset_label} - spindle",
            include_dimensions,
            include_titles,
            compatibility_mode,
        ),
        dxf_version=dxf_version,
    )
    written.append(str(spindle_path))

    for index, rammer in enumerate(model.rammers, start=1):
        file_path = output_dir / f"{index:02d}-{slugify(rammer.key)}{suffix}.dxf"
        _draw_part_document(
            file_path,
            unit,
            include_dimensions,
            lambda msp, rammer=rammer: _draw_rammer(
                msp,
                rammer,
                0.0,
                0.0,
                f"{preset_label} - {rammer.label}",
                include_dimensions,
                include_titles,
                compatibility_mode,
            ),
            dxf_version=dxf_version,
        )
        written.append(str(file_path))

    return written


def _write_combined_dxf(
    path: Path,
    model: ToolModel,
    preset_label: str,
    unit: str,
    include_dimensions: bool,
    dxf_version: str = "R2010",
) -> str:
    doc = _new_doc(unit, include_dimensions, dxf_version=dxf_version)
    msp = doc.modelspace()
    cursor = 0.0
    top = 0.0
    spacing = model.params.a * (4.5 if include_dimensions else 2.5)
    compatibility_mode = (not include_dimensions) or dxf_version == "R12"
    include_titles = include_dimensions

    _draw_spindle(
        msp,
        model.spindle,
        cursor,
        top,
        f"{preset_label} - spindle",
        include_dimensions,
        include_titles,
        compatibility_mode,
    )
    cursor += model.params.a + spacing

    for rammer in model.rammers:
        _draw_rammer(
            msp,
            rammer,
            cursor,
            top,
            f"{preset_label} - {rammer.label}",
            include_dimensions,
            include_titles,
            compatibility_mode,
        )
        cursor += model.params.a + spacing

    if include_dimensions:
        notes_x = cursor + model.params.a
        notes_y = 0.0
        overview_title = [
            f"{preset_label.upper()} TOOLING SET - A = {_format_length(model.params.a)} IN",
            "UNITS: INCHES" if unit == "in" else "UNITS: MILLIMETERS",
            "DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.",
            "ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.",
            "ALL TRANSVERSE WIDTH DIMENSIONS ACROSS CENTERLINE ARE DIAMETERS.",
            "ALL DIAMETERS AND BORES CONCENTRIC TO CENTERLINE.",
            "ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.",
            "BORE DEPTHS ARE MEASURED FROM WORKING END.",
            "RAMMERS ARE SHOWN WORKING END DOWN.",
            "SPINDLE IS SHOWN COLLAR END DOWN.",
            f"DO-NOT-PASS MARK LOCATED {_format_length(model.head_length)} FROM TOP FACE OF EACH RAMMER.",
            "SCRIBE DO-NOT-PASS LINE 360 DEG AROUND EACH RAMMER.",
            "BREAK ALL SHARP EDGES.",
            "MATERIAL: SPECIFY",
            "FINISH: SPECIFY",
            "UNLESS OTHERWISE SPECIFIED: ADD TOLERANCE.",
        ]
        _add_multiline_notes(msp, overview_title, notes_x, notes_y, height=0.085, line_spacing=0.13)

        table_top = notes_y - 1.8
        row_height = 0.22
        col_widths = [0.5, 2.0, 1.1, 0.95, 1.2, 1.15, 2.4]
        headers = ["P", "NAME", "OD", "OAL", "BORE OD", "BORE DP", "NOTES"]
        rows = [
            [
                "1",
                "SPINDLE",
                _format_diameter(model.spindle.tube_diameter),
                _format_length(model.spindle.total_length),
                "-",
                "-",
                f"ROOT {_format_diameter(model.spindle.root_diameter)} TIP {_format_diameter(model.spindle.tip_diameter)}",
            ]
        ]
        for index, rammer in enumerate(model.rammers, start=2):
            note = "DO-NOT-PASS MARK"
            if rammer.has_taper:
                note = f"I {_format_length(rammer.nose_angle)} DEG"
            rows.append(
                [
                    str(index),
                    rammer.label.upper().replace("FULL-DEPTH ", "FULL ").replace("PROGRESSIVE ", "PROG "),
                    _format_diameter(rammer.outer_diameter),
                    _format_length(rammer.overall_length),
                    _format_diameter(rammer.bore_diameter) if rammer.bore_diameter > 0 else "-",
                    _format_length(rammer.bore_depth) if rammer.bore_depth > 0 else "-",
                    note,
                ]
            )

        table_width = sum(col_widths)
        table_height = row_height * (len(rows) + 1)
        x = notes_x
        y = table_top
        msp.add_line((x, y), (x + table_width, y), dxfattribs={"layer": LAYER_TABLE})
        for row_index in range(len(rows) + 2):
            yy = y - row_index * row_height
            msp.add_line((x, yy), (x + table_width, yy), dxfattribs={"layer": LAYER_TABLE})
        cursor_x = x
        for width in [0.0] + col_widths:
            msp.add_line((cursor_x, y), (cursor_x, y - table_height), dxfattribs={"layer": LAYER_TABLE})
            cursor_x += width
        msp.add_line((x + table_width, y), (x + table_width, y - table_height), dxfattribs={"layer": LAYER_TABLE})

        text_x = x + 0.05
        running_xs = [x + 0.05]
        cx = x
        for width in col_widths[:-1]:
            cx += width
            running_xs.append(cx + 0.05)
        for col_index, header in enumerate(headers):
            _add_note_line(msp, header, running_xs[col_index], y - 0.16, 0.075)
        for row_index, row in enumerate(rows, start=1):
            yy = y - row_height * row_index - 0.16
            for col_index, cell in enumerate(row):
                _add_note_line(msp, cell, running_xs[col_index], yy, 0.07)

    zoom.extents(msp, factor=1.05)
    _update_header_extents(doc, msp)
    doc.saveas(path)
    return str(path)


def _write_solid_exports(output_dir: Path, model: ToolModel, assumption: AssumptionSet) -> tuple[str, list[str], str, list[str]]:
    solids_dir = ensure_directory(output_dir / "solids")
    separate_steps: list[str] = []
    separate_stls: list[str] = []
    solids: list[tuple[str, cq.Workplane]] = [("spindle", _build_spindle_solid(model.spindle))]

    for rammer in model.rammers:
        solids.append((slugify(rammer.key), _build_rammer_solid(rammer, assumption)))

    for name, solid in solids:
        step_path = solids_dir / f"{name}.step"
        stl_path = solids_dir / f"{name}.stl"
        _write_step(step_path, solid)
        _write_stl(stl_path, solid)
        separate_steps.append(str(step_path))
        separate_stls.append(str(stl_path))

    combined = _compound_layout(solids, model.params.a * 1.5)
    combined_step = solids_dir / "tooling-set.step"
    combined_stl = solids_dir / "tooling-set.stl"
    _write_step(combined_step, combined)
    _write_stl(combined_stl, combined)
    return str(combined_step), separate_steps, str(combined_stl), separate_stls


def _write_manifest(
    path: Path,
    params: ToolParams,
    assumption: AssumptionSet,
    preset: PresetDefinition | None,
    unit: str,
    model: ToolModel,
) -> str:
    payload = {
        "unit": unit,
        "preset": preset.key if preset else "custom",
        "assumption": asdict(assumption),
        "params": asdict(params),
        "derived": {
            "head_length": model.head_length,
            "spindle_tip_diameter": model.spindle.tip_diameter,
            "spindle_collar_rise": model.spindle.collar_rise,
            "rammers": [asdict(rammer) for rammer in model.rammers],
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def export_tooling_set(
    *,
    output_dir: Path,
    params: ToolParams,
    assumption: AssumptionSet = BASELINE_ASSUMPTION,
    unit: str = "in",
    preset: PresetDefinition | None = None,
) -> ExportBundle:
    output_dir = ensure_directory(output_dir)
    drawings_dir = ensure_directory(output_dir / "drawings")
    model = build_tool_model(params, assumption)

    combined_dxf = _write_combined_dxf(
        drawings_dir / "tooling-set.dxf",
        model,
        preset.label if preset else "Custom",
        unit,
        False,
    )
    combined_fusion_dxf = _write_combined_dxf(
        drawings_dir / "tooling-set-fusion-r12.dxf",
        model,
        preset.label if preset else "Custom",
        unit,
        False,
        "R12",
    )
    combined_annotated_dxf = _write_combined_dxf(
        drawings_dir / "tooling-set-annotated.dxf",
        model,
        preset.label if preset else "Custom",
        unit,
        True,
    )
    separate_dxfs = _write_separate_dxf(drawings_dir, model, preset.label if preset else "Custom", unit, False)
    separate_fusion_dxfs = _write_separate_dxf(
        drawings_dir,
        model,
        preset.label if preset else "Custom",
        unit,
        False,
        dxf_version="R12",
        suffix_override="-fusion-r12",
    )
    separate_annotated_dxfs = _write_separate_dxf(drawings_dir, model, preset.label if preset else "Custom", unit, True)

    scale = _length_scale(unit)
    scaled_model = ToolModel(
        params=model.params,
        assumption=model.assumption,
        head_length=model.head_length * scale,
        spindle=_scaled_spindle(model.spindle, scale),
        rammers=[_scaled_rammer(rammer, scale) for rammer in model.rammers],
    )
    combined_step, separate_steps, combined_stl, separate_stls = _write_solid_exports(output_dir, scaled_model, assumption)

    openscad_path = output_dir / "tooling-set.scad"
    _write_openscad(openscad_path, model, preset, assumption, unit)
    manifest_path = output_dir / "tooling-set.json"
    manifest = _write_manifest(manifest_path, params, assumption, preset, unit, model)

    return ExportBundle(
        output_dir=str(output_dir),
        combined_dxf=combined_dxf,
        combined_annotated_dxf=combined_annotated_dxf,
        combined_fusion_dxf=combined_fusion_dxf,
        separate_dxfs=separate_dxfs,
        separate_annotated_dxfs=separate_annotated_dxfs,
        separate_fusion_dxfs=separate_fusion_dxfs,
        combined_step=combined_step,
        separate_steps=separate_steps,
        combined_stl=combined_stl,
        separate_stls=separate_stls,
        openscad=str(openscad_path),
        manifest=manifest,
    )
