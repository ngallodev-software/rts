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
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

from .model import (
    BASELINE_ASSUMPTION,
    MM_PER_INCH,
    AssumptionSet,
    ExportBundle,
    ManufacturingSettings,
    RammerModel,
    SpindleModel,
    ToolModel,
    ToolParams,
    build_tool_model,
    default_manufacturing_settings,
)
from .presets import PresetDefinition
from .versioning import load_version_manifest, write_version_manifest


LAYER_PROFILE = "PROFILE"
LAYER_HIDDEN = "HIDDEN"
LAYER_CENTER = "CENTER"
LAYER_DIM = "DIM"
LAYER_TEXT = "TEXT"
LAYER_TITLE = "TITLE"
LAYER_MARKS = "MARKS"
LAYER_NOTES = "NOTES"
LAYER_TABLE = "TABLE"
QA_APPID = "RTS_QA"

# Text/dimension sizes are intentionally conservative for a machinist-readable
# combined sheet. Keep these in drawing units so small 0.75 in tooling is not
# overwhelmed by the annotations, but avoid the very small text from the first
# prototype.
TITLE_TEXT_HEIGHT = 0.105
NOTE_TEXT_HEIGHT = 0.09
TABLE_TEXT_HEIGHT = 0.078
DIM_TEXT_HEIGHT = 0.10
LEADER_TEXT_HEIGHT = 0.085
ANNOTATED_ZONE_MIN_GAP = 0.50


def format_value(value: float) -> str:
    text = f"{value:.4f}"
    return text.rstrip("0").rstrip(".")


def slugify(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _setup_layers(doc: ezdxf.EzDxfDocument) -> None:
    if QA_APPID not in doc.appids:
        doc.appids.add(QA_APPID)
    if "HIDDEN" not in doc.linetypes:
        doc.linetypes.add("HIDDEN", pattern=[0.25, 0.125, -0.125], description="Hidden __ __ __")
    if "CENTER" not in doc.linetypes:
        doc.linetypes.add("CENTER", pattern=[0.5, 0.25, -0.10, 0.05, -0.10], description="Center ____ _ ____")
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
        doc.header["$DIMPOST"] = "<> mm" if unit == "mm" else "<> in"
        doc.header["$DIMAPOST"] = "<>°"
        _normalize_dimstyles(doc, unit)
    return doc


def _normalize_dimstyles(doc: ezdxf.EzDxfDocument, unit: str | None = None) -> None:
    if unit is None:
        unit = "mm" if doc.header.get("$INSUNITS", 1) == 4 else "in"
    for name in ("EZDXF", "EZ_CURVED"):
        if name in doc.dimstyles:
            style = doc.dimstyles.get(name)
            style.dxf.dimlfac = 1.0
            style.dxf.dimdec = 3
            style.dxf.dimzin = 8
            style.dxf.dimdsep = ord(".")
            style.dxf.dimasz = 0.175
            style.dxf.dimtxt = DIM_TEXT_HEIGHT
            style.dxf.dimpost = "<> mm" if unit == "mm" else "<> in"


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
        override={"dimtad": 1, "dimtxt": DIM_TEXT_HEIGHT, "dimlfac": 1.0, "dimdec": 3, "dimzin": 8},
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
        override={"dimtad": 1, "dimtxt": DIM_TEXT_HEIGHT, "dimlfac": 1.0, "dimdec": 3, "dimzin": 8},
    )
    dim.render()


def _add_title(msp: ezdxf.layouts.Modelspace, text: str, x: float, y: float) -> None:
    msp.add_text(text, dxfattribs={"height": TITLE_TEXT_HEIGHT, "layer": LAYER_TITLE}).set_placement((x, y))


def _add_note_line(msp: ezdxf.layouts.Modelspace, text: str, x: float, y: float, height: float = NOTE_TEXT_HEIGHT) -> None:
    msp.add_text(text, dxfattribs={"height": height, "layer": LAYER_NOTES}).set_placement((x, y))


def _add_multiline_notes(
    msp: ezdxf.layouts.Modelspace,
    lines: list[str],
    x: float,
    y: float,
    height: float = NOTE_TEXT_HEIGHT,
    line_spacing: float = 0.13,
) -> None:
    cursor = y
    for line in lines:
        _add_note_line(msp, line, x, cursor, height)
        cursor -= line_spacing


def _add_leader_callout(
    msp: ezdxf.layouts.Modelspace,
    text: str,
    target: tuple[float, float],
    text_position: tuple[float, float],
    *,
    height: float = LEADER_TEXT_HEIGHT,
) -> None:
    """Add a simple machinist-friendly leader line with nearby text.

    This intentionally uses primitive LINE/TEXT entities instead of richer
    MLEADER objects so Fusion 360, SolidWorks, Solid Edge, and FreeCAD are
    more likely to import the annotation predictably.
    """
    tx, ty = text_position
    landing = (tx - 0.08 if tx >= target[0] else tx + 0.08, ty)
    msp.add_line(target, landing, dxfattribs={"layer": LAYER_DIM})
    msp.add_text(text, dxfattribs={"height": height, "layer": LAYER_TEXT}).set_placement((tx, ty))


PDF_MARGIN_PT = 36.0
PDF_MIN_TEXT_PT = 6.5
PDF_LINE_WIDTH_PT = 0.65


class _PdfSheet:
    def __init__(self, unit: str) -> None:
        self.unit = unit
        self.scale = 72.0 if unit == "in" else 72.0 / MM_PER_INCH
        self.elements: list[tuple] = []
        self.min_x = math.inf
        self.max_x = -math.inf
        self.min_y = math.inf
        self.max_y = -math.inf

    def _include_point(self, x: float, y: float) -> None:
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)

    def _include_text_box(self, x: float, y: float, text: str, height: float, font_name: str = "Helvetica") -> None:
        font_size = max(height * self.scale, PDF_MIN_TEXT_PT)
        width = stringWidth(text, font_name, font_size) / self.scale
        self._include_point(x, y)
        self._include_point(x + width, y + height)

    def bounds(self) -> tuple[float, float, float, float]:
        if self.min_x is math.inf:
            return (0.0, 0.0, 0.0, 0.0)
        return self.min_x, self.max_x, self.min_y, self.max_y

    def transformed(self, dx: float = 0.0, dy: float = 0.0, scale: float = 1.0) -> list[tuple]:
        transformed: list[tuple] = []
        for element in self.elements:
            kind = element[0]
            if kind == "line":
                _, start, end, width, dash = element
                transformed.append(
                    (
                        "line",
                        (start[0] * scale + dx, start[1] * scale + dy),
                        (end[0] * scale + dx, end[1] * scale + dy),
                        width,
                        dash,
                    )
                )
            elif kind == "polyline":
                _, points, closed, width = element
                transformed.append(
                    (
                        "polyline",
                        [(x * scale + dx, y * scale + dy) for x, y in points],
                        closed,
                        width,
                    )
                )
            elif kind == "rect":
                _, lower_left, upper_right, width = element
                transformed.append(
                    (
                        "rect",
                        (lower_left[0] * scale + dx, lower_left[1] * scale + dy),
                        (upper_right[0] * scale + dx, upper_right[1] * scale + dy),
                        width,
                    )
                )
            elif kind == "text":
                _, position, text, height, font_name, rotation, align = element
                transformed.append(
                    (
                        "text",
                        (position[0] * scale + dx, position[1] * scale + dy),
                        text,
                        height * scale,
                        font_name,
                        rotation,
                        align,
                    )
                )
        return transformed

    def line(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        *,
        width: float = PDF_LINE_WIDTH_PT,
        dash: tuple[float, ...] | None = None,
    ) -> None:
        self._include_point(*start)
        self._include_point(*end)
        self.elements.append(("line", start, end, width, dash))

    def polyline(
        self,
        points: list[tuple[float, float]],
        *,
        closed: bool = False,
        width: float = PDF_LINE_WIDTH_PT,
    ) -> None:
        for point in points:
            self._include_point(*point)
        self.elements.append(("polyline", points, closed, width))

    def text(
        self,
        position: tuple[float, float],
        text: str,
        *,
        height: float = NOTE_TEXT_HEIGHT,
        font_name: str = "Helvetica",
        rotation: float = 0.0,
        align: str = "left",
    ) -> None:
        x, y = position
        self._include_text_box(x, y, text, height, font_name)
        self.elements.append(("text", position, text, height, font_name, rotation, align))

    def rect(self, lower_left: tuple[float, float], upper_right: tuple[float, float], *, width: float = PDF_LINE_WIDTH_PT) -> None:
        x1, y1 = lower_left
        x2, y2 = upper_right
        self._include_point(x1, y1)
        self._include_point(x2, y2)
        self.elements.append(("rect", lower_left, upper_right, width))

    def render(self, path: Path) -> None:
        if not self.elements:
            raise ValueError("PDF sheet has no geometry to render.")
        page_w_pt, page_h_pt = landscape(letter)
        content_w_pt = page_w_pt - PDF_MARGIN_PT * 2
        content_h_pt = page_h_pt - PDF_MARGIN_PT * 2
        content_w_units = content_w_pt / self.scale
        content_h_units = content_h_pt / self.scale
        total_w_units = max(self.max_x - self.min_x, content_w_units)
        total_h_units = max(self.max_y - self.min_y, content_h_units)
        cols = max(1, math.ceil(total_w_units / content_w_units))
        rows = max(1, math.ceil(total_h_units / content_h_units))
        page = pdf_canvas.Canvas(str(path), pagesize=landscape(letter))
        page.setTitle(path.stem)
        page.setAuthor("RTS exporter")

        pages = [(col, row) for row in reversed(range(rows)) for col in range(cols)]
        total_pages = len(pages)

        for page_index, (col, row) in enumerate(pages, start=1):
            tile_min_x = self.min_x + col * content_w_units
            tile_min_y = self.min_y + row * content_h_units
            tile_max_x = tile_min_x + content_w_units
            tile_max_y = tile_min_y + content_h_units

            def tx(x: float) -> float:
                return PDF_MARGIN_PT + (x - tile_min_x) * self.scale

            def ty(y: float) -> float:
                return PDF_MARGIN_PT + (y - tile_min_y) * self.scale

            page.saveState()
            clip = page.beginPath()
            clip.rect(PDF_MARGIN_PT, PDF_MARGIN_PT, content_w_pt, content_h_pt)
            page.clipPath(clip, stroke=0, fill=0)
            page.setStrokeColor(colors.black)
            page.setFillColor(colors.black)

            for element in self.elements:
                kind = element[0]
                if kind == "line":
                    _, start, end, width, dash = element
                    if max(start[0], end[0]) < tile_min_x or min(start[0], end[0]) > tile_max_x:
                        continue
                    if max(start[1], end[1]) < tile_min_y or min(start[1], end[1]) > tile_max_y:
                        continue
                    page.setLineWidth(width)
                    if dash:
                        page.setDash(*dash)
                    else:
                        page.setDash()
                    page.line(tx(start[0]), ty(start[1]), tx(end[0]), ty(end[1]))
                elif kind == "polyline":
                    _, points, closed, width = element
                    xs = [point[0] for point in points]
                    ys = [point[1] for point in points]
                    if max(xs) < tile_min_x or min(xs) > tile_max_x or max(ys) < tile_min_y or min(ys) > tile_max_y:
                        continue
                    page.setLineWidth(width)
                    page.setDash()
                    poly = page.beginPath()
                    poly.moveTo(tx(points[0][0]), ty(points[0][1]))
                    for point in points[1:]:
                        poly.lineTo(tx(point[0]), ty(point[1]))
                    if closed:
                        poly.close()
                    page.drawPath(poly, stroke=1, fill=0)
                elif kind == "rect":
                    _, lower_left, upper_right, width = element
                    x1, y1 = lower_left
                    x2, y2 = upper_right
                    if x2 < tile_min_x or x1 > tile_max_x or y2 < tile_min_y or y1 > tile_max_y:
                        continue
                    page.setLineWidth(width)
                    page.setDash()
                    page.rect(tx(x1), ty(y1), (x2 - x1) * self.scale, (y2 - y1) * self.scale, stroke=1, fill=0)
                elif kind == "text":
                    _, position, text, height, font_name, rotation, align = element
                    font_size = max(height * self.scale, PDF_MIN_TEXT_PT)
                    page.setDash()
                    page.setFont(font_name, font_size)
                    page.saveState()
                    page.translate(tx(position[0]), ty(position[1]))
                    if rotation:
                        page.rotate(rotation)
                    text_width = stringWidth(text, font_name, font_size)
                    dx = 0.0
                    if align == "center":
                        dx = -text_width / 2
                    elif align == "right":
                        dx = -text_width
                    page.drawString(dx, 0, text)
                    page.restoreState()

            page.restoreState()
            page.setDash()
            page.setFont("Helvetica", 7)
            page.drawRightString(page_w_pt - PDF_MARGIN_PT, 18, f"{path.stem}  page {page_index}/{total_pages}")
            page.showPage()
        page.save()


def _draw_pdf_elements(page: pdf_canvas.Canvas, elements: list[tuple]) -> None:
    page.setStrokeColor(colors.black)
    page.setFillColor(colors.black)
    for element in elements:
        kind = element[0]
        if kind == "line":
            _, start, end, width, dash = element
            page.setLineWidth(width)
            if dash:
                page.setDash(*dash)
            else:
                page.setDash()
            page.line(start[0], start[1], end[0], end[1])
        elif kind == "polyline":
            _, points, closed, width = element
            page.setLineWidth(width)
            page.setDash()
            poly = page.beginPath()
            poly.moveTo(points[0][0], points[0][1])
            for point in points[1:]:
                poly.lineTo(point[0], point[1])
            if closed:
                poly.close()
            page.drawPath(poly, stroke=1, fill=0)
        elif kind == "rect":
            _, lower_left, upper_right, width = element
            x1, y1 = lower_left
            x2, y2 = upper_right
            page.setLineWidth(width)
            page.setDash()
            page.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=0)
        elif kind == "text":
            _, position, text, height, font_name, rotation, align = element
            page.setDash()
            page.setFont(font_name, height)
            page.saveState()
            page.translate(position[0], position[1])
            if rotation:
                page.rotate(rotation)
            text_width = stringWidth(text, font_name, height)
            dx = 0.0
            if align == "center":
                dx = -text_width / 2
            elif align == "right":
                dx = -text_width
            page.drawString(dx, 0, text)
            page.restoreState()


def _fit_elements_to_box(sheet: _PdfSheet, box: tuple[float, float, float, float], padding: float = 0.12) -> list[tuple]:
    min_x, max_x, min_y, max_y = sheet.bounds()
    box_x, box_y, box_w, box_h = box
    width = max(max_x - min_x, 0.0001)
    height = max(max_y - min_y, 0.0001)
    scale = min((box_w - padding * 2) / width, (box_h - padding * 2) / height)
    draw_w = width * scale
    draw_h = height * scale
    offset_x = box_x + (box_w - draw_w) / 2 - min_x * scale
    offset_y = box_y + (box_h - draw_h) / 2 - min_y * scale
    return sheet.transformed(offset_x, offset_y, scale)


def _render_fixed_page(
    path: Path,
    *,
    title: str,
    subtitle: str | None = None,
    elements: list[tuple],
    footnote: str | None = None,
) -> None:
    page_w_pt, page_h_pt = landscape(letter)
    page = pdf_canvas.Canvas(str(path), pagesize=landscape(letter))
    page.setTitle(title)
    page.setAuthor("RTS exporter")
    _draw_pdf_elements(page, elements)
    if subtitle:
        page.setFont("Helvetica", 8)
        page.drawCentredString(page_w_pt / 2, page_h_pt - 20, subtitle)
    if footnote:
        page.setFont("Helvetica", 7)
        page.drawRightString(page_w_pt - PDF_MARGIN_PT, 18, footnote)
    page.showPage()
    page.save()


def _pdf_add_title(sheet: _PdfSheet, text: str, x: float, y: float) -> None:
    sheet.text((x, y), text, height=TITLE_TEXT_HEIGHT)


def _pdf_add_note_line(sheet: _PdfSheet, text: str, x: float, y: float, height: float = NOTE_TEXT_HEIGHT) -> None:
    sheet.text((x, y), text, height=height)


def _pdf_add_multiline_notes(
    sheet: _PdfSheet,
    lines: list[str],
    x: float,
    y: float,
    height: float = NOTE_TEXT_HEIGHT,
    line_spacing: float = 0.13,
) -> None:
    cursor = y
    for line in lines:
        _pdf_add_note_line(sheet, line, x, cursor, height)
        cursor -= line_spacing


def _pdf_add_leader_callout(
    sheet: _PdfSheet,
    text: str,
    target: tuple[float, float],
    text_position: tuple[float, float],
    *,
    height: float = LEADER_TEXT_HEIGHT,
) -> None:
    tx, ty = text_position
    landing = (tx - 0.08 if tx >= target[0] else tx + 0.08, ty)
    sheet.line(target, landing)
    sheet.text((tx, ty), text, height=height)


def _pdf_render_linear_dim(
    sheet: _PdfSheet,
    p1: tuple[float, float],
    p2: tuple[float, float],
    location: tuple[float, float],
    angle: float = 0.0,
) -> None:
    if angle == 90:
        x = location[0]
        y1, y2 = p1[1], p2[1]
        sheet.line((p1[0], y1), (x, y1))
        sheet.line((p2[0], y2), (x, y2))
        sheet.line((x, y1), (x, y2))
        text = _format_measurement(abs(y2 - y1), sheet.unit)
        sheet.text((x + 0.07, (y1 + y2) / 2 - 0.03), text, height=DIM_TEXT_HEIGHT, rotation=90)
        return

    y = location[1]
    x1, x2 = p1[0], p2[0]
    sheet.line((x1, p1[1]), (x1, y))
    sheet.line((x2, p2[1]), (x2, y))
    sheet.line((x1, y), (x2, y))
    text = _format_measurement(abs(x2 - x1), sheet.unit)
    sheet.text(((x1 + x2) / 2, y + 0.03), text, height=DIM_TEXT_HEIGHT, align="center")


def _pdf_draw_hidden_bore(
    sheet: _PdfSheet,
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
    dash = (4.0, 2.5)
    sheet.line((left, top), (left, bottom), dash=dash)
    sheet.line((right, top), (right, bottom), dash=dash)
    sheet.line((left, top), (right, top), dash=dash)


def _format_diameter(value: float) -> str:
    return f"%%c{value:.3f}"


def _format_diameter_pdf(value: float) -> str:
    return f"Ø{value:.3f}"


def _format_length(value: float) -> str:
    return f"{value:.3f}"


def _format_measurement(value: float, unit: str) -> str:
    return f"{value:.3f} {'mm' if unit == 'mm' else 'in'}"


def _format_diameter_measurement(value: float, unit: str, *, pdf: bool = False) -> str:
    diameter = "Ø" if pdf else "%%c"
    return f"{diameter}{value:.3f} {'mm' if unit == 'mm' else 'in'}"


def _format_surface_finish(value: float, unit: str) -> str:
    return f"Ra {value:g} {'µm' if unit == 'mm' else 'µin'}"


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
    """Return the 2D rammer profile in the model coordinate convention.

    y=0 is the handle/top end. y=overall_length is the working/bore-opening
    end. The full-depth A rammer taper belongs at the working end and
    terminates at the bore opening, matching the original RTS art and the
    current manufacturing interpretation.
    """
    half_outer = rammer.outer_diameter / 2
    if rammer.has_taper and rammer.taper_height > 0:
        taper_start = max(rammer.overall_length - rammer.taper_height, 0.0)
        return [
            (-half_outer, 0.0),
            (half_outer, 0.0),
            (half_outer, taper_start),
            (rammer.bore_diameter / 2, rammer.overall_length),
            (-rammer.bore_diameter / 2, rammer.overall_length),
            (-half_outer, taper_start),
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
        switch_mark_from_top=None if rammer.switch_mark_from_top is None else rammer.switch_mark_from_top * factor,
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


def _reserve_next_annotated_zone(
    msp: ezdxf.layouts.Modelspace,
    start_index: int,
    previous_max_x: float | None,
    tube_diameter: float,
    zone_key: str,
) -> tuple[float, float]:
    """Return the current zone's right edge and a safe origin for the next part."""
    entities = list(msp)[start_index:]
    for entity in entities:
        entity.set_xdata(QA_APPID, [(1000, zone_key)])
    extents = bbox.extents(entities, fast=True)
    min_x = extents.extmin.x
    max_x = extents.extmax.x
    gap = max(ANNOTATED_ZONE_MIN_GAP, tube_diameter * 0.75)
    if previous_max_x is not None and min_x < previous_max_x + gap - 1e-6:
        raise RuntimeError(
            f"Annotated part zones overlap: next zone begins at {min_x:.4f}, "
            f"but must begin at or after {previous_max_x + gap:.4f}."
        )
    left_reach = tube_diameter / 2 + max(1.60, tube_diameter * 0.50)
    return max_x, max_x + gap + left_reach


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
    unit: str,
    manufacturing: ManufacturingSettings,
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
        _add_title(msp, title, min_x, max_y + 0.75)

    if not include_dimensions:
        return

    straight_height = max(spindle.collar_height - spindle.collar_rise, 0.0)
    tip_y = origin_y
    root_y = origin_y - spindle.spindle_length
    collar_taper_end_y = origin_y - (spindle.spindle_length + spindle.collar_rise)
    base_y = origin_y - spindle.total_length
    spindle_mid_y = (tip_y + root_y) / 2
    collar_mid_y = (root_y + base_y) / 2
    collar_straight_mid_y = (collar_taper_end_y + base_y) / 2 if straight_height > 0 else collar_mid_y

    # Length dimensions. Diameter dimensions are leader callouts below so they
    # do not sit on top of the profile or get swapped between spindle stations.
    _render_linear_dim(
        msp,
        (max_x, tip_y),
        (max_x, base_y),
        (min_x - 1.45, (tip_y + base_y) / 2),
        angle=90,
    )
    _render_linear_dim(
        msp,
        (origin_x + spindle.root_diameter / 2, tip_y),
        (origin_x + spindle.root_diameter / 2, root_y),
        (min_x - 1.05, spindle_mid_y),
        angle=90,
    )
    _render_linear_dim(
        msp,
        (min_x, root_y),
        (min_x, base_y),
        (min_x - 0.65, collar_mid_y),
        angle=90,
    )
    if spindle.collar_rise > 0:
        _render_linear_dim(
            msp,
            (max_x, root_y),
            (max_x, collar_taper_end_y),
            (min_x - 0.25, (root_y + collar_taper_end_y) / 2),
            angle=90,
        )

    _add_leader_callout(
        msp,
        f"TIP OD {_format_diameter_measurement(spindle.tip_diameter, unit)} +0.000/-{manufacturing.spindle_minus_tolerance:.3f}",
        (origin_x + spindle.tip_diameter / 2, tip_y),
        (max_x + 1.25, tip_y + 0.18),
    )
    _add_leader_callout(
        msp,
        f"ROOT OD {_format_diameter_measurement(spindle.root_diameter, unit)} +0.000/-{manufacturing.spindle_minus_tolerance:.3f}",
        (origin_x + spindle.root_diameter / 2, root_y),
        (max_x + 1.25, root_y + 0.20),
    )
    _add_leader_callout(
        msp,
        f"COLLAR OD {_format_diameter_measurement(spindle.tube_diameter, unit)}",
        (origin_x + spindle.tube_diameter / 2, collar_straight_mid_y),
        (max_x + 1.25, root_y - 0.48),
    )
    _add_leader_callout(
        msp,
        f"SPINDLE TAPER {_format_length(_spindle_taper_per_side(spindle))}°/SIDE",
        (origin_x + (spindle.root_diameter + spindle.tip_diameter) / 4, spindle_mid_y),
        (max_x + 1.25, spindle_mid_y - 0.2),
    )
    if spindle.collar_rise > 0:
        _add_leader_callout(
            msp,
            f"COLLAR TAPER {_format_length(_collar_taper_from_shoulder_face(spindle))}° FROM SHOULDER FACE",
            (origin_x + (spindle.tube_diameter + spindle.root_diameter) / 4, (root_y + collar_taper_end_y) / 2),
            (max_x + 1.25, root_y - 0.22),
        )

    notes = [
        "PART 1 - SPINDLE / CORE FORMER",
        f"COLLAR HEIGHT {_format_measurement(spindle.collar_height, unit)}",
        f"SHOULDER AXIAL LENGTH {_format_measurement(spindle.collar_rise, unit)}",
        f"SPINDLE LENGTH {_format_measurement(spindle.spindle_length, unit)}",
        f"OVERALL LENGTH {_format_measurement(spindle.total_length, unit)}",
        f"SPINDLE SURFACES: POLISH TO {_format_surface_finish(manufacturing.spindle_finish_ra, unit)} OR BETTER",
        "REMOVE BURRS; BREAK SHARP EDGES 0.005 in MAX" if unit == "in" else "REMOVE BURRS; BREAK SHARP EDGES 0.13 mm MAX",
        "SPINDLE SHOWN TIP UP / COLLAR BASE DOWN",
        "LEGACY RTS ORIENTATION; OFFSET LOWER ON COMBINED SHEET",
    ]
    _add_multiline_notes(msp, notes, max_x + 3.25, max_y - 0.1, height=NOTE_TEXT_HEIGHT, line_spacing=0.14)


def _draw_rammer(
    msp: ezdxf.layouts.Modelspace,
    rammer: RammerModel,
    origin_x: float,
    origin_y: float,
    title: str,
    include_dimensions: bool,
    include_titles: bool,
    compatibility_mode: bool,
    unit: str,
    manufacturing: ManufacturingSettings,
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
        if rammer.switch_mark_from_top is not None:
            switch_y = origin_y - rammer.switch_mark_from_top
            msp.add_line(
                (origin_x - rammer.outer_diameter / 2, switch_y),
                (origin_x + rammer.outer_diameter / 2, switch_y),
                dxfattribs={"layer": LAYER_MARKS},
            )
    if include_titles:
        _add_title(msp, title, min_x, max_y + 0.75)

    if not include_dimensions:
        return

    top_y = origin_y
    working_y = origin_y - rammer.overall_length
    head_y = origin_y - rammer.head_length
    groove_y = origin_y - rammer.groove_from_top
    switch_y = None if rammer.switch_mark_from_top is None else origin_y - rammer.switch_mark_from_top

    _render_linear_dim(msp, (min_x, max_y), (max_x, max_y), (origin_x, max_y + 0.45), angle=0)
    _render_linear_dim(msp, (max_x, max_y), (max_x, min_y), (min_x - 1.15, (max_y + min_y) / 2), angle=90)
    _render_linear_dim(
        msp,
        (origin_x + rammer.outer_diameter / 2, top_y),
        (origin_x + rammer.outer_diameter / 2, head_y),
        (max_x + 0.55, (top_y + head_y) / 2),
        angle=90,
    )
    if abs(rammer.groove_from_top - rammer.head_length) > 1e-6:
        _render_linear_dim(
            msp,
            (origin_x + rammer.outer_diameter / 2, top_y),
            (origin_x + rammer.outer_diameter / 2, groove_y),
            (max_x + 0.55, (top_y + groove_y) / 2),
            angle=90,
        )

    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        _render_linear_dim(
            msp,
            (origin_x - rammer.bore_diameter / 2, working_y),
            (origin_x + rammer.bore_diameter / 2, working_y),
            (origin_x, working_y - 0.45),
            angle=0,
        )
        _render_linear_dim(
            msp,
            (origin_x + rammer.bore_diameter / 2, working_y),
            (origin_x + rammer.bore_diameter / 2, origin_y - (rammer.overall_length - rammer.bore_depth)),
            (max_x + 0.95, origin_y - (rammer.overall_length - rammer.bore_depth / 2)),
            angle=90,
        )
    if switch_y is not None:
        _render_linear_dim(
            msp,
            (min_x, top_y),
            (min_x, switch_y),
            (min_x - 0.65, (top_y + switch_y) / 2),
            angle=90,
        )
    if rammer.has_taper and rammer.taper_height > 0:
        taper_start_y = working_y + rammer.taper_height
        _render_linear_dim(
            msp,
            (min_x, taper_start_y),
            (min_x, working_y),
            (max_x + 0.25, (taper_start_y + working_y) / 2),
            angle=90,
        )

    notes = [
        f"OD {_format_diameter_measurement(rammer.outer_diameter, unit)} ±{manufacturing.general_tolerance:.3f}",
        f"OAL {_format_measurement(rammer.overall_length, unit)}",
        f"DO-NOT-PASS MARK {_format_measurement(rammer.groove_from_top, unit)} FROM HANDLE/TOP FACE",
        "RAMMER SHOWN HANDLE END UP / WORKING END DOWN",
    ]
    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        notes.extend(
            [
                f"BORE BASIC {_format_diameter_measurement(rammer.bore_diameter, unit)} x {_format_measurement(rammer.bore_depth, unit)} DEEP",
                f"BORE LIMIT +{manufacturing.minimum_diametral_clearance + manufacturing.bore_plus_tolerance:.3f}/+{manufacturing.minimum_diametral_clearance:.3f} {unit}",
                "STRAIGHT CYLINDRICAL BORE OPEN FROM WORKING END",
            ]
        )
    if rammer.has_taper and rammer.taper_height > 0:
        notes.extend(
            [
                f"{_format_length(rammer.nose_angle)}° BACKSIDE NOZZLE TAPER",
                f"TIP TAPER AXIAL LENGTH {_format_measurement(rammer.taper_height, unit)}",
                f"TAPER TO {_format_diameter_measurement(rammer.bore_diameter, unit)} BORE OPENING",
                "NO FLAT LAND AT BORE OPENING",
            ]
        )
        taper_target = (
            origin_x + (rammer.outer_diameter + rammer.bore_diameter) / 4,
            origin_y - (rammer.overall_length - rammer.taper_height / 2),
        )
    if rammer.switch_mark_from_top is not None:
        notes.insert(4, f"SWITCH-RAMMER MARK {_format_measurement(rammer.switch_mark_from_top, unit)} FROM HANDLE/TOP FACE")
    notes.extend(
        [
            f"POLISH OUTSIDE TO {_format_surface_finish(manufacturing.rammer_od_finish_ra, unit)} OR BETTER",
            f"BORE UNIFORM, SMOOTH, AND {_format_surface_finish(manufacturing.rammer_bore_finish_ra, unit)} OR BETTER" if rammer.bore_depth > 0 else "",
            "REMOVE ALL BURRS; DEBUR BORE MOUTH WITHOUT ROUNDING WORKING PROFILE",
        ]
    )
    notes = [line for line in notes if line]
    _add_multiline_notes(msp, [f"PART - {rammer.label.upper()}"] + notes, max_x + 2.25, max_y - 0.1, height=NOTE_TEXT_HEIGHT, line_spacing=0.14)


def _draw_spindle_pdf(
    sheet: _PdfSheet,
    spindle: SpindleModel,
    origin_x: float,
    origin_y: float,
    title: str,
    include_dimensions: bool,
    include_titles: bool,
    unit: str,
    manufacturing: ManufacturingSettings,
) -> None:
    raw_points = _spindle_outline_points(spindle)
    points = [(origin_x + x, origin_y - y) for x, y in raw_points]
    sheet.polyline(points, closed=True)
    min_x, max_x, min_y, max_y = _part_bounds(points)
    sheet.line((origin_x, max_y + 0.35), (origin_x, min_y - 0.35), dash=(6.0, 3.0))
    if include_titles:
        _pdf_add_title(sheet, title, min_x, max_y + 0.75)

    if not include_dimensions:
        return

    straight_height = max(spindle.collar_height - spindle.collar_rise, 0.0)
    tip_y = origin_y
    root_y = origin_y - spindle.spindle_length
    collar_taper_end_y = origin_y - (spindle.spindle_length + spindle.collar_rise)
    base_y = origin_y - spindle.total_length
    spindle_mid_y = (tip_y + root_y) / 2
    collar_mid_y = (root_y + base_y) / 2
    collar_straight_mid_y = (collar_taper_end_y + base_y) / 2 if straight_height > 0 else collar_mid_y

    _pdf_render_linear_dim(sheet, (max_x, tip_y), (max_x, base_y), (min_x - 1.45, (tip_y + base_y) / 2), angle=90)
    _pdf_render_linear_dim(
        sheet,
        (origin_x + spindle.root_diameter / 2, tip_y),
        (origin_x + spindle.root_diameter / 2, root_y),
        (min_x - 1.05, spindle_mid_y),
        angle=90,
    )
    _pdf_render_linear_dim(sheet, (min_x, root_y), (min_x, base_y), (min_x - 0.65, collar_mid_y), angle=90)
    if spindle.collar_rise > 0:
        _pdf_render_linear_dim(
            sheet,
            (max_x, root_y),
            (max_x, collar_taper_end_y),
            (min_x - 0.25, (root_y + collar_taper_end_y) / 2),
            angle=90,
        )

    _pdf_add_leader_callout(
        sheet,
        f"TIP OD {_format_diameter_measurement(spindle.tip_diameter, unit, pdf=True)} +0.000/-{manufacturing.spindle_minus_tolerance:.3f}",
        (origin_x + spindle.tip_diameter / 2, tip_y),
        (max_x + 1.25, tip_y + 0.18),
    )
    _pdf_add_leader_callout(
        sheet,
        f"ROOT OD {_format_diameter_measurement(spindle.root_diameter, unit, pdf=True)} +0.000/-{manufacturing.spindle_minus_tolerance:.3f}",
        (origin_x + spindle.root_diameter / 2, root_y),
        (max_x + 1.25, root_y + 0.20),
    )
    _pdf_add_leader_callout(
        sheet,
        f"COLLAR OD {_format_diameter_measurement(spindle.tube_diameter, unit, pdf=True)}",
        (origin_x + spindle.tube_diameter / 2, collar_straight_mid_y),
        (max_x + 1.25, root_y - 0.48),
    )
    _pdf_add_leader_callout(
        sheet,
        f"SPINDLE TAPER {_format_length(_spindle_taper_per_side(spindle))}°/SIDE",
        (origin_x + (spindle.root_diameter + spindle.tip_diameter) / 4, spindle_mid_y),
        (max_x + 1.25, spindle_mid_y - 0.2),
    )
    if spindle.collar_rise > 0:
        _pdf_add_leader_callout(
            sheet,
            f"COLLAR TAPER {_format_length(_collar_taper_from_shoulder_face(spindle))}° FROM SHOULDER FACE",
            (origin_x + (spindle.tube_diameter + spindle.root_diameter) / 4, (root_y + collar_taper_end_y) / 2),
            (max_x + 1.25, root_y - 0.22),
        )

    notes = [
        "PART 1 - SPINDLE / CORE FORMER",
        f"COLLAR HEIGHT {_format_measurement(spindle.collar_height, unit)}",
        f"SHOULDER AXIAL LENGTH {_format_measurement(spindle.collar_rise, unit)}",
        f"SPINDLE LENGTH {_format_measurement(spindle.spindle_length, unit)}",
        f"OVERALL LENGTH {_format_measurement(spindle.total_length, unit)}",
        f"SPINDLE SURFACES: POLISH TO {_format_surface_finish(manufacturing.spindle_finish_ra, unit)} OR BETTER",
        "REMOVE BURRS; BREAK SHARP EDGES 0.005 in MAX" if unit == "in" else "REMOVE BURRS; BREAK SHARP EDGES 0.13 mm MAX",
        "SPINDLE SHOWN TIP UP / COLLAR BASE DOWN",
        "LEGACY RTS ORIENTATION; OFFSET LOWER ON COMBINED SHEET",
    ]
    _pdf_add_multiline_notes(sheet, notes, max_x + 3.25, max_y - 0.1, height=NOTE_TEXT_HEIGHT, line_spacing=0.14)


def _draw_rammer_pdf(
    sheet: _PdfSheet,
    rammer: RammerModel,
    origin_x: float,
    origin_y: float,
    title: str,
    include_dimensions: bool,
    include_titles: bool,
    unit: str,
    manufacturing: ManufacturingSettings,
) -> None:
    raw_points = _rammer_outline_points(rammer)
    points = [(origin_x + x, origin_y - y) for x, y in raw_points]
    sheet.polyline(points, closed=True)
    _pdf_draw_hidden_bore(sheet, rammer.bore_diameter, rammer.bore_depth, rammer.overall_length, origin_x, origin_y)
    min_x, max_x, min_y, max_y = _part_bounds(points)
    sheet.line((origin_x, max_y + 0.35), (origin_x, min_y - 0.35), dash=(6.0, 3.0))
    mark_y = origin_y - rammer.groove_from_top
    sheet.line((origin_x - rammer.outer_diameter / 2, mark_y), (origin_x + rammer.outer_diameter / 2, mark_y))
    if rammer.switch_mark_from_top is not None:
        switch_mark_y = origin_y - rammer.switch_mark_from_top
        sheet.line((origin_x - rammer.outer_diameter / 2, switch_mark_y), (origin_x + rammer.outer_diameter / 2, switch_mark_y))
    if include_titles:
        _pdf_add_title(sheet, title, min_x, max_y + 0.75)

    if not include_dimensions:
        return

    top_y = origin_y
    working_y = origin_y - rammer.overall_length
    head_y = origin_y - rammer.head_length
    groove_y = origin_y - rammer.groove_from_top
    switch_y = None if rammer.switch_mark_from_top is None else origin_y - rammer.switch_mark_from_top

    _pdf_render_linear_dim(sheet, (min_x, max_y), (max_x, max_y), (origin_x, max_y + 0.45), angle=0)
    _pdf_render_linear_dim(sheet, (max_x, max_y), (max_x, min_y), (min_x - 1.15, (max_y + min_y) / 2), angle=90)
    _pdf_render_linear_dim(
        sheet,
        (origin_x + rammer.outer_diameter / 2, top_y),
        (origin_x + rammer.outer_diameter / 2, head_y),
        (max_x + 0.55, (top_y + head_y) / 2),
        angle=90,
    )
    if abs(rammer.groove_from_top - rammer.head_length) > 1e-6:
        _pdf_render_linear_dim(
            sheet,
            (origin_x + rammer.outer_diameter / 2, top_y),
            (origin_x + rammer.outer_diameter / 2, groove_y),
            (max_x + 0.55, (top_y + groove_y) / 2),
            angle=90,
        )

    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        _pdf_render_linear_dim(
            sheet,
            (origin_x - rammer.bore_diameter / 2, working_y),
            (origin_x + rammer.bore_diameter / 2, working_y),
            (origin_x, working_y - 0.45),
            angle=0,
        )
        _pdf_render_linear_dim(
            sheet,
            (origin_x + rammer.bore_diameter / 2, working_y),
            (origin_x + rammer.bore_diameter / 2, origin_y - (rammer.overall_length - rammer.bore_depth)),
            (max_x + 0.95, origin_y - (rammer.overall_length - rammer.bore_depth / 2)),
            angle=90,
        )
    if switch_y is not None:
        _pdf_render_linear_dim(sheet, (min_x, top_y), (min_x, switch_y), (min_x - 0.65, (top_y + switch_y) / 2), angle=90)
    if rammer.has_taper and rammer.taper_height > 0:
        taper_start_y = working_y + rammer.taper_height
        _pdf_render_linear_dim(sheet, (max_x, taper_start_y), (max_x, working_y), (max_x + 0.25, (taper_start_y + working_y) / 2), angle=90)

    notes = [
        f"OD {_format_diameter_measurement(rammer.outer_diameter, unit, pdf=True)} ±{manufacturing.general_tolerance:.3f}",
        f"OAL {_format_measurement(rammer.overall_length, unit)}",
        f"DO-NOT-PASS MARK {_format_measurement(rammer.groove_from_top, unit)} FROM HANDLE/TOP FACE",
        "RAMMER SHOWN HANDLE END UP / WORKING END DOWN",
    ]
    if rammer.bore_depth > 0 and rammer.bore_diameter > 0:
        notes.extend(
            [
                f"BORE BASIC {_format_diameter_measurement(rammer.bore_diameter, unit, pdf=True)} x {_format_measurement(rammer.bore_depth, unit)} DEEP",
                f"BORE LIMIT +{manufacturing.minimum_diametral_clearance + manufacturing.bore_plus_tolerance:.3f}/+{manufacturing.minimum_diametral_clearance:.3f} {unit}",
                "STRAIGHT CYLINDRICAL BORE OPEN FROM WORKING END",
            ]
        )
    if rammer.has_taper and rammer.taper_height > 0:
        notes.extend(
            [
                f"{_format_length(rammer.nose_angle)}° BACKSIDE NOZZLE TAPER",
                f"TIP TAPER AXIAL LENGTH {_format_measurement(rammer.taper_height, unit)}",
                f"TAPER TO {_format_diameter_measurement(rammer.bore_diameter, unit, pdf=True)} BORE OPENING",
                "NO FLAT LAND AT BORE OPENING",
            ]
        )
        taper_target = (
            origin_x + (rammer.outer_diameter + rammer.bore_diameter) / 4,
            origin_y - (rammer.overall_length - rammer.taper_height / 2),
        )
    if rammer.switch_mark_from_top is not None:
        notes.insert(4, f"SWITCH-RAMMER MARK {_format_measurement(rammer.switch_mark_from_top, unit)} FROM HANDLE/TOP FACE")
    notes.extend(
        [
            f"POLISH OUTSIDE TO {_format_surface_finish(manufacturing.rammer_od_finish_ra, unit)} OR BETTER",
            f"BORE UNIFORM, SMOOTH, AND {_format_surface_finish(manufacturing.rammer_bore_finish_ra, unit)} OR BETTER" if rammer.bore_depth > 0 else "",
            "REMOVE ALL BURRS; DEBUR BORE MOUTH WITHOUT ROUNDING WORKING PROFILE",
        ]
    )
    notes = [line for line in notes if line]
    _pdf_add_multiline_notes(sheet, [f"PART - {rammer.label.upper()}"] + notes, max_x + 2.25, max_y - 0.1, height=NOTE_TEXT_HEIGHT, line_spacing=0.14)


def _write_pdf_document(path: Path, unit: str, draw_callback) -> str:
    sheet = _PdfSheet(unit)
    draw_callback(sheet)
    sheet.render(path)
    return str(path)


def _write_separate_pdf(
    output_dir: Path,
    model: ToolModel,
    preset_label: str,
    unit: str,
    suffix_override: str | None = None,
) -> list[str]:
    written: list[str] = []
    suffix = suffix_override if suffix_override is not None else "-annotated"
    page_w_pt, page_h_pt = landscape(letter)
    full_box = (PDF_MARGIN_PT, PDF_MARGIN_PT, page_w_pt - PDF_MARGIN_PT * 2, page_h_pt - PDF_MARGIN_PT * 2)

    spindle_path = output_dir / f"spindle{suffix}.pdf"
    spindle_sheet = _PdfSheet(unit)
    _draw_spindle_pdf(spindle_sheet, model.spindle, 0.0, 0.0, f"{preset_label} - spindle", True, True, unit, model.manufacturing)
    spindle_page = _fit_elements_to_box(spindle_sheet, full_box)
    _render_fixed_page(spindle_path, title=f"{preset_label} - spindle", elements=spindle_page, footnote=f"{spindle_path.stem}")
    written.append(str(spindle_path))

    for index, rammer in enumerate(model.rammers, start=1):
        file_path = output_dir / f"{index:02d}-{slugify(rammer.key)}{suffix}.pdf"
        rammer_sheet = _PdfSheet(unit)
        _draw_rammer_pdf(rammer_sheet, rammer, 0.0, 0.0, f"{preset_label} - {rammer.label}", True, True, unit, model.manufacturing)
        rammer_page = _fit_elements_to_box(rammer_sheet, full_box)
        _render_fixed_page(file_path, title=f"{preset_label} - {rammer.label}", elements=rammer_page, footnote=f"{file_path.stem}")
        written.append(str(file_path))

    return written


def _write_combined_pdf(path: Path, model: ToolModel, preset_label: str, unit: str) -> str:
    page_w_pt, page_h_pt = landscape(letter)
    margin = PDF_MARGIN_PT
    gutter = 18.0
    cell_w = (page_w_pt - margin * 2 - gutter) / 2
    cell_h = page_h_pt - margin * 2 - 24.0
    full_box = (margin, margin, page_w_pt - margin * 2, page_h_pt - margin * 2 - 20.0)
    left_box = (margin, margin, cell_w, cell_h)
    right_box = (margin + cell_w + gutter, margin, cell_w, cell_h)

    parts: list[tuple[str, _PdfSheet]] = []
    spindle_sheet = _PdfSheet(unit)
    _draw_spindle_pdf(spindle_sheet, model.spindle, 0.0, 0.0, f"{preset_label} - spindle", True, True, unit, model.manufacturing)
    parts.append(("spindle", spindle_sheet))
    for rammer in model.rammers:
        rammer_sheet = _PdfSheet(unit)
        _draw_rammer_pdf(rammer_sheet, rammer, 0.0, 0.0, f"{preset_label} - {rammer.label}", True, True, unit, model.manufacturing)
        parts.append((rammer.key, rammer_sheet))

    page1 = _fit_elements_to_box(parts[0][1], left_box) + _fit_elements_to_box(parts[1][1], right_box)
    page2 = _fit_elements_to_box(parts[2][1], left_box) + _fit_elements_to_box(parts[3][1], right_box)
    page3 = _fit_elements_to_box(parts[4][1], full_box)

    page = pdf_canvas.Canvas(str(path), pagesize=landscape(letter))
    page.setTitle(f"{preset_label} tooling set")
    page.setAuthor("RTS exporter")
    for index, elements in enumerate([page1, page2, page3], start=1):
        _draw_pdf_elements(page, elements)
        page.setFont("Helvetica", 8)
        page.drawString(margin, page_h_pt - 16, f"{preset_label} tooling set")
        page.drawRightString(page_w_pt - margin, 18, f"{path.stem}  page {index}/4")
        page.showPage()

    table_sheet = _PdfSheet(unit)
    notes_x = margin
    notes_y = page_h_pt - margin - 0.35
    overview_title = [
        f"{preset_label.upper()} TOOLING SET - A = {_format_measurement(model.params.a, unit)}",
        "UNITS: INCHES" if unit == "in" else "UNITS: MILLIMETERS",
        "DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.",
        "DRAFTING CONVENTIONS INFORMED BY ASME Y14.5; SURFACE TEXTURE TERMS BY ASME B46.1.",
        "ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.",
        "ALL TRANSVERSE WIDTH DIMENSIONS ACROSS CENTERLINE ARE DIAMETERS.",
        "ALL DIAMETERS AND BORES CONCENTRIC TO CENTERLINE.",
        "ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.",
        "BORE DEPTHS ARE MEASURED FROM WORKING END.",
        "RAMMERS ARE SHOWN HANDLE END UP / WORKING END DOWN.",
        "SPINDLE SHOWN TIP UP / COLLAR BASE DOWN; OFFSET LOWER TO MATCH ORIGINAL ART.",
        "FULL-DEPTH A RAMMER TAPER IS AT WORKING/BORE-OPENING END.",
        f"DO-NOT-PASS MARK LOCATED {_format_measurement(model.head_length, unit)} FROM HANDLE/TOP FACE OF EACH RAMMER.",
        f"SWITCH MARK IS {model.manufacturing.switch_mark_offset_diameters:g} TUBE I.D. FARTHER TOWARD WORKING END; OMIT ON FINAL RAMMER.",
        "SCRIBE/ETCH BOTH MARKS 360° AROUND RAMMERS; MARKS ARE NOT FIT FEATURES.",
        f"GENERAL LINEAR TOLERANCE ±{model.manufacturing.general_tolerance:.3f} {unit} UNLESS SPECIFIC LIMITS ARE SHOWN.",
        f"MINIMUM SPINDLE-TO-BORE DIAMETRAL CLEARANCE {model.manufacturing.minimum_diametral_clearance:.3f} {unit}.",
        "REMOVE ALL BURRS AND BREAK SHARP EDGES WITHOUT ALTERING WORKING PROFILES.",
        "MATERIAL: SPECIFY",
        f"SPINDLE/RAMMER OD FINISH {_format_surface_finish(model.manufacturing.spindle_finish_ra, unit)} OR BETTER.",
        f"RAMMER BORE FINISH {_format_surface_finish(model.manufacturing.rammer_bore_finish_ra, unit)} OR BETTER; UNIFORM AND SMOOTH.",
    ]
    _pdf_add_multiline_notes(table_sheet, overview_title, notes_x, notes_y, height=NOTE_TEXT_HEIGHT, line_spacing=0.14)

    table_top = notes_y - 3.35
    row_height = 0.25
    col_widths = [0.55, 2.25, 1.15, 1.0, 1.25, 1.2, 3.45]
    headers = ["P", "NAME", "OD", "OAL", "BORE OD", "BORE DP", "NOTES"]
    rows = [
        [
            "1",
            "SPINDLE",
            _format_diameter_pdf(model.spindle.tube_diameter),
            _format_length(model.spindle.total_length),
            "-",
            "-",
            f"ROOT {_format_diameter_pdf(model.spindle.root_diameter)} TIP {_format_diameter_pdf(model.spindle.tip_diameter)} F {_format_length(model.spindle.collar_height)}",
        ]
    ]
    for index, rammer in enumerate(model.rammers, start=2):
        note = "DO-NOT-PASS MARK"
        if rammer.has_taper:
            note = f"I {_format_length(rammer.nose_angle)}°"
        rows.append(
            [
                str(index),
                rammer.label.upper().replace("FULL-DEPTH ", "FULL ").replace("PROGRESSIVE ", "PROG "),
                _format_diameter_pdf(rammer.outer_diameter),
                _format_length(rammer.overall_length),
                _format_diameter_pdf(rammer.bore_diameter) if rammer.bore_diameter > 0 else "-",
                _format_length(rammer.bore_depth) if rammer.bore_depth > 0 else "-",
                note,
            ]
        )

    table_width = sum(col_widths)
    table_height = row_height * (len(rows) + 1)
    x = notes_x
    y = table_top
    table_sheet.line((x, y), (x + table_width, y))
    for row_index in range(len(rows) + 2):
        yy = y - row_index * row_height
        table_sheet.line((x, yy), (x + table_width, yy))
    cursor_x = x
    for width in [0.0] + col_widths:
        table_sheet.line((cursor_x, y), (cursor_x, y - table_height))
        cursor_x += width
    table_sheet.line((x + table_width, y), (x + table_width, y - table_height))

    running_xs = [x + 0.05]
    cx = x
    for width in col_widths[:-1]:
        cx += width
        running_xs.append(cx + 0.05)
    for col_index, header in enumerate(headers):
        _pdf_add_note_line(table_sheet, header, running_xs[col_index], y - 0.17, TABLE_TEXT_HEIGHT)
    for row_index, row in enumerate(rows, start=1):
        yy = y - row_height * row_index - 0.16
        for col_index, cell in enumerate(row):
            _pdf_add_note_line(table_sheet, cell, running_xs[col_index], yy, TABLE_TEXT_HEIGHT)

    table_elements = _fit_elements_to_box(table_sheet, full_box)
    _draw_pdf_elements(page, table_elements)
    page.setFont("Helvetica", 8)
    page.drawString(margin, page_h_pt - 16, f"{preset_label} tooling set")
    page.drawRightString(page_w_pt - margin, 18, f"{path.stem}  page 4/4")
    page.showPage()
    page.save()
    return str(path)


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
            unit,
            model.manufacturing,
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
                unit,
                model.manufacturing,
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
    spacing = model.params.a * 2.5
    compatibility_mode = (not include_dimensions) or dxf_version == "R12"
    include_titles = include_dimensions

    longest_rammer = max((rammer.overall_length for rammer in model.rammers), default=model.spindle.total_length)
    spindle_drop = max(longest_rammer - model.spindle.total_length, 0.0) + (model.params.a * 0.5 if include_dimensions else model.params.a * 0.25)
    spindle_top = top - spindle_drop

    zone_start = len(msp)
    _draw_spindle(
        msp,
        model.spindle,
        cursor,
        spindle_top,
        f"{preset_label} - spindle",
        include_dimensions,
        include_titles,
        compatibility_mode,
        unit,
        model.manufacturing,
    )
    previous_max_x: float | None = None
    if include_dimensions:
        previous_max_x, cursor = _reserve_next_annotated_zone(
            msp,
            zone_start,
            previous_max_x,
            model.params.a,
            "spindle",
        )
    else:
        cursor += model.params.a + spacing

    for rammer in model.rammers:
        zone_start = len(msp)
        _draw_rammer(
            msp,
            rammer,
            cursor,
            top,
            f"{preset_label} - {rammer.label}",
            include_dimensions,
            include_titles,
            compatibility_mode,
            unit,
            model.manufacturing,
        )
        if include_dimensions:
            previous_max_x, cursor = _reserve_next_annotated_zone(
                msp,
                zone_start,
                previous_max_x,
                model.params.a,
                rammer.key,
            )
        else:
            cursor += model.params.a + spacing

    if include_dimensions:
        overview_start = len(msp)
        notes_x = (previous_max_x or cursor) + max(ANNOTATED_ZONE_MIN_GAP, model.params.a * 0.75)
        notes_y = 0.0
        overview_title = [
            f"{preset_label.upper()} TOOLING SET - A = {_format_measurement(model.params.a, unit)}",
            "UNITS: INCHES" if unit == "in" else "UNITS: MILLIMETERS",
            "DISPLAYED DIMENSIONS ARE FINISHED TOOLING DIMENSIONS.",
            "DRAFTING CONVENTIONS INFORMED BY ASME Y14.5; SURFACE TEXTURE TERMS BY ASME B46.1.",
            "ALL PARTS ARE AXISYMMETRIC ABOUT SHOWN CENTERLINES.",
            "ALL TRANSVERSE WIDTH DIMENSIONS ACROSS CENTERLINE ARE DIAMETERS.",
            "ALL DIAMETERS AND BORES CONCENTRIC TO CENTERLINE.",
            "ALL RAMMER BORES ARE STRAIGHT CYLINDRICAL AND OPEN FROM WORKING END.",
            "BORE DEPTHS ARE MEASURED FROM WORKING END.",
            "RAMMERS ARE SHOWN HANDLE END UP / WORKING END DOWN.",
            "SPINDLE SHOWN TIP UP / COLLAR BASE DOWN; OFFSET LOWER TO MATCH ORIGINAL ART.",
            "FULL-DEPTH A RAMMER TAPER IS AT WORKING/BORE-OPENING END.",
            f"DO-NOT-PASS MARK LOCATED {_format_measurement(model.head_length, unit)} FROM HANDLE/TOP FACE OF EACH RAMMER.",
            f"SWITCH MARK IS {model.manufacturing.switch_mark_offset_diameters:g} TUBE I.D. FARTHER TOWARD WORKING END; OMIT ON FINAL RAMMER.",
            "SCRIBE/ETCH BOTH MARKS 360° AROUND RAMMERS; MARKS ARE NOT FIT FEATURES.",
            f"GENERAL LINEAR TOLERANCE ±{model.manufacturing.general_tolerance:.3f} {unit} UNLESS SPECIFIC LIMITS ARE SHOWN.",
            f"MINIMUM SPINDLE-TO-BORE DIAMETRAL CLEARANCE {model.manufacturing.minimum_diametral_clearance:.3f} {unit}.",
            "REMOVE ALL BURRS AND BREAK SHARP EDGES WITHOUT ALTERING WORKING PROFILES.",
            "MATERIAL: SPECIFY",
            f"SPINDLE/RAMMER OD FINISH {_format_surface_finish(model.manufacturing.spindle_finish_ra, unit)} OR BETTER.",
            f"RAMMER BORE FINISH {_format_surface_finish(model.manufacturing.rammer_bore_finish_ra, unit)} OR BETTER; UNIFORM AND SMOOTH.",
        ]
        _add_multiline_notes(msp, overview_title, notes_x, notes_y, height=NOTE_TEXT_HEIGHT, line_spacing=0.14)

        table_top = notes_y - 3.35
        row_height = 0.25
        col_widths = [0.55, 2.25, 1.15, 1.0, 1.25, 1.2, 3.45]
        headers = ["P", "NAME", "OD", "OAL", "BORE OD", "BORE DP", "NOTES"]
        rows = [
            [
                "1",
                "SPINDLE",
                _format_diameter(model.spindle.tube_diameter),
                _format_length(model.spindle.total_length),
                "-",
                "-",
                f"ROOT {_format_diameter(model.spindle.root_diameter)} TIP {_format_diameter(model.spindle.tip_diameter)} F {_format_length(model.spindle.collar_height)}",
            ]
        ]
        for index, rammer in enumerate(model.rammers, start=2):
            note = "DO-NOT-PASS MARK"
            if rammer.has_taper:
                note = f"I {_format_length(rammer.nose_angle)}°"
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
            _add_note_line(msp, header, running_xs[col_index], y - 0.17, TABLE_TEXT_HEIGHT)
        for row_index, row in enumerate(rows, start=1):
            yy = y - row_height * row_index - 0.16
            for col_index, cell in enumerate(row):
                _add_note_line(msp, cell, running_xs[col_index], yy, TABLE_TEXT_HEIGHT)
        _reserve_next_annotated_zone(
            msp,
            overview_start,
            previous_max_x,
            model.params.a,
            "overview",
        )

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
        "versions": load_version_manifest(),
        "unit": unit,
        "preset": preset.key if preset else "custom",
        "assumption": asdict(assumption),
        "manufacturing": asdict(model.manufacturing),
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
    manufacturing: ManufacturingSettings | None = None,
) -> ExportBundle:
    output_dir = ensure_directory(output_dir)
    drawings_dir = ensure_directory(output_dir / "drawings")
    model = build_tool_model(params, assumption, manufacturing or default_manufacturing_settings("mm" if unit == "mm" else "in"))

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
    combined_annotated_pdf = _write_combined_pdf(
        drawings_dir / "tooling-set-annotated.pdf",
        model,
        preset.label if preset else "Custom",
        unit,
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
    separate_annotated_pdfs = _write_separate_pdf(drawings_dir, model, preset.label if preset else "Custom", unit)

    scale = _length_scale(unit)
    scaled_model = ToolModel(
        params=model.params,
        assumption=model.assumption,
        manufacturing=model.manufacturing,
        head_length=model.head_length * scale,
        spindle=_scaled_spindle(model.spindle, scale),
        rammers=[_scaled_rammer(rammer, scale) for rammer in model.rammers],
    )
    combined_step, separate_steps, combined_stl, separate_stls = _write_solid_exports(output_dir, scaled_model, assumption)

    openscad_path = output_dir / "tooling-set.scad"
    _write_openscad(openscad_path, model, preset, assumption, unit)
    manifest_path = output_dir / "tooling-set.json"
    manifest = _write_manifest(manifest_path, params, assumption, preset, unit, model)
    version_manifest = write_version_manifest(output_dir / "version-manifest.json")

    return ExportBundle(
        output_dir=str(output_dir),
        combined_dxf=combined_dxf,
        combined_annotated_dxf=combined_annotated_dxf,
        combined_annotated_pdf=combined_annotated_pdf,
        combined_fusion_dxf=combined_fusion_dxf,
        separate_dxfs=separate_dxfs,
        separate_annotated_dxfs=separate_annotated_dxfs,
        separate_annotated_pdfs=separate_annotated_pdfs,
        separate_fusion_dxfs=separate_fusion_dxfs,
        combined_step=combined_step,
        separate_steps=separate_steps,
        combined_stl=combined_stl,
        separate_stls=separate_stls,
        openscad=str(openscad_path),
        manifest=manifest,
        version_manifest=version_manifest,
    )
