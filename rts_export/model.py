from __future__ import annotations

from dataclasses import asdict, dataclass
from math import radians, tan
from typing import Literal


Unit = Literal["in", "mm"]
AngleConvention = Literal["from_axis", "from_face", "from_shoulder_face", "included_angle"]
GrooveMode = Literal["line", "v-groove"]
RammerRole = Literal["solid", "fullDepth", "progressive"]

MM_PER_INCH = 25.4
HEAD_RATIO = 1.5


@dataclass(frozen=True)
class ToolParams:
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    g: float
    h: int
    i: float

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class ManufacturingSettings:
    general_tolerance: float
    spindle_minus_tolerance: float
    bore_plus_tolerance: float
    minimum_diametral_clearance: float
    switch_mark_offset_diameters: float
    spindle_finish_ra: float
    rammer_od_finish_ra: float
    rammer_bore_finish_ra: float


def default_manufacturing_settings(unit: Unit = "in") -> ManufacturingSettings:
    if unit == "mm":
        return ManufacturingSettings(0.05, 0.025, 0.025, 0.10, 1.0, 0.8, 0.8, 1.6)
    return ManufacturingSettings(0.002, 0.001, 0.001, 0.004, 1.0, 32.0, 32.0, 63.0)


def validate_manufacturing_settings(settings: ManufacturingSettings, tube_diameter: float) -> None:
    values = asdict(settings)
    for key, value in values.items():
        if value < 0:
            raise ValueError(f"{key.replace('_', ' ')} cannot be negative.")
    if settings.minimum_diametral_clearance <= 0:
        raise ValueError("Minimum diametral clearance must be greater than zero.")
    if settings.switch_mark_offset_diameters <= 0:
        raise ValueError("Switch-mark offset must be greater than zero.")
    if settings.minimum_diametral_clearance > tube_diameter * 0.10:
        raise ValueError("Minimum diametral clearance cannot exceed 10% of tube I.D.")
    if settings.general_tolerance > tube_diameter * 0.05:
        raise ValueError("General tolerance cannot exceed 5% of tube I.D.")


@dataclass(frozen=True)
class AssumptionSet:
    key: str
    label: str
    notes: str
    angle_e: AngleConvention
    angle_g: AngleConvention
    angle_i: AngleConvention
    groove_mode: GrooveMode
    draw_physical_groove: bool


@dataclass(frozen=True)
class SpindleModel:
    tube_diameter: float
    collar_height: float
    spindle_length: float
    root_diameter: float
    tip_diameter: float
    total_length: float
    collar_rise: float
    points: list[tuple[float, float]]


@dataclass(frozen=True)
class RammerModel:
    key: str
    label: str
    role: RammerRole
    overall_length: float
    outer_diameter: float
    head_length: float
    groove_from_top: float
    switch_mark_from_top: float | None
    bore_depth: float
    bore_diameter: float
    nose_angle: float
    taper_height: float
    has_taper: bool
    points: list[tuple[float, float]]


@dataclass(frozen=True)
class ToolModel:
    params: ToolParams
    assumption: AssumptionSet
    manufacturing: ManufacturingSettings
    head_length: float
    spindle: SpindleModel
    rammers: list[RammerModel]


@dataclass(frozen=True)
class ExportBundle:
    output_dir: str
    combined_dxf: str
    combined_annotated_dxf: str
    combined_annotated_pdf: str
    combined_fusion_dxf: str
    separate_dxfs: list[str]
    separate_annotated_dxfs: list[str]
    separate_annotated_pdfs: list[str]
    separate_fusion_dxfs: list[str]
    combined_step: str
    separate_steps: list[str]
    combined_stl: str
    separate_stls: list[str]
    openscad: str
    manifest: str
    version_manifest: str


BASELINE_ASSUMPTION = AssumptionSet(
    key="baseline",
    label="Baseline",
    notes="E from axis, G from shoulder face, I from face, do-not-pass mark drawn as a scribed line by default.",
    angle_e="from_axis",
    angle_g="from_shoulder_face",
    angle_i="from_face",
    groove_mode="line",
    draw_physical_groove=False,
)


HARNESS_ASSUMPTIONS = {
    BASELINE_ASSUMPTION.key: BASELINE_ASSUMPTION,
    "e-included": AssumptionSet(
        key="e-included",
        label="E as included angle",
        notes="Halves the per-side spindle taper to test a misread drafting convention.",
        angle_e="included_angle",
        angle_g="from_shoulder_face",
        angle_i="from_face",
        groove_mode="line",
        draw_physical_groove=False,
    ),
    "g-from-axis": AssumptionSet(
        key="g-from-axis",
        label="G from axis",
        notes="Treats collar taper as an axial taper instead of a shoulder-face angle.",
        angle_e="from_axis",
        angle_g="from_axis",
        angle_i="from_face",
        groove_mode="line",
        draw_physical_groove=False,
    ),
    "i-from-axis": AssumptionSet(
        key="i-from-axis",
        label="I from axis",
        notes="Tests whether the first rammer taper is measured from the axis rather than the lower face.",
        angle_e="from_axis",
        angle_g="from_shoulder_face",
        angle_i="from_axis",
        groove_mode="line",
        draw_physical_groove=False,
    ),
    "groove-line-only": AssumptionSet(
        key="groove-line-only",
        label="Groove as scribed line",
        notes="Suppresses any physical groove notch and keeps only a drawn mark.",
        angle_e="from_axis",
        angle_g="from_shoulder_face",
        angle_i="from_face",
        groove_mode="line",
        draw_physical_groove=False,
    ),
    "groove-v-groove": AssumptionSet(
        key="groove-v-groove",
        label="Groove as shallow V-groove",
        notes="Models the do-not-pass mark as a shallow machined V-groove for comparison/export testing.",
        angle_e="from_axis",
        angle_g="from_shoulder_face",
        angle_i="from_face",
        groove_mode="v-groove",
        draw_physical_groove=True,
    ),
}


def round_value(value: float, digits: int) -> float:
    factor = 10**digits
    return round(value * factor) / factor


def convert_params(params: ToolParams, next_unit: Unit) -> ToolParams:
    factor = MM_PER_INCH if next_unit == "mm" else 1 / MM_PER_INCH
    digits = 2 if next_unit == "mm" else 4
    return ToolParams(
        a=round_value(params.a * factor, digits),
        b=round_value(params.b * factor, digits),
        c=round_value(params.c * factor, digits),
        d=round_value(params.d * factor, digits),
        e=params.e,
        f=round_value(params.f * factor, digits),
        g=params.g,
        h=int(round(params.h)),
        i=params.i,
    )


def normalize_angle(angle: float, mode: AngleConvention) -> float:
    if mode == "included_angle":
        return angle / 2
    return angle


def tan_deg(value: float) -> float:
    return tan(radians(value))


def spindle_tip_diameter(params: ToolParams, assumption: AssumptionSet) -> float:
    angle = normalize_angle(params.e, assumption.angle_e)
    return max(params.d - 2 * params.c * tan_deg(angle), 0.0)


def collar_rise(params: ToolParams, assumption: AssumptionSet) -> float:
    if params.g == 0:
        return 0.0
    angle = normalize_angle(params.g, assumption.angle_g)
    if assumption.angle_g == "from_axis":
        return ((params.a - params.d) / 2) / max(tan_deg(90 - angle), 0.0001)
    return ((params.a - params.d) / 2) * tan_deg(angle)


def build_spindle(params: ToolParams, assumption: AssumptionSet) -> SpindleModel:
    tip_diameter = spindle_tip_diameter(params, assumption)
    rise = collar_rise(params, assumption)
    shoulder_y = -(params.f - rise)
    return SpindleModel(
        tube_diameter=params.a,
        collar_height=params.f,
        spindle_length=params.c,
        root_diameter=params.d,
        tip_diameter=tip_diameter,
        total_length=params.c + params.f,
        collar_rise=rise,
        points=[
            (params.a / 2, 0),
            (params.a / 2, shoulder_y),
            (params.d / 2, -params.f),
            (tip_diameter / 2, -(params.f + params.c)),
            (-tip_diameter / 2, -(params.f + params.c)),
            (-params.d / 2, -params.f),
            (-params.a / 2, shoulder_y),
            (-params.a / 2, 0),
        ],
    )


def first_rammer_taper_height(params: ToolParams, assumption: AssumptionSet) -> float:
    angle = normalize_angle(params.i, assumption.angle_i)
    if params.i == 0 or angle == 0:
        return 0.0
    radial_run = (params.a - params.d) / 2
    if assumption.angle_i == "from_axis":
        rise = radial_run * tan_deg(angle)
    else:
        rise = radial_run / max(tan_deg(angle), 0.0001)
    return max(min(rise, params.b + params.a * HEAD_RATIO), 0.0)


def add_groove(points: list[tuple[float, float]], outer_radius: float, groove_y: float) -> list[tuple[float, float]]:
    updated: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        if index == 2:
            inset = outer_radius * 0.06
            groove_height = outer_radius * 0.04
            updated.append((point[0], groove_y + groove_height))
            updated.append((point[0] - inset, groove_y))
            updated.append((point[0], groove_y - groove_height))
        updated.append(point)
    return updated


def build_rammer(
    key: str,
    label: str,
    role: RammerRole,
    overall_length: float,
    outer_diameter: float,
    head_length: float,
    groove_from_top: float,
    switch_mark_from_top: float | None,
    bore_depth: float,
    bore_diameter: float,
    assumption: AssumptionSet,
    nose_angle: float = 0.0,
) -> RammerModel:
    half_outer = outer_diameter / 2
    taper_height = 0.0
    if role == "fullDepth" and nose_angle > 0:
        taper_height = first_rammer_taper_height(
            ToolParams(
                a=outer_diameter,
                b=overall_length,
                c=bore_depth,
                d=bore_diameter,
                e=0,
                f=0,
                g=0,
                h=0,
                i=nose_angle,
            ),
            assumption,
        )
        body_end = overall_length - taper_height
        points = [
            (-half_outer, 0),
            (half_outer, 0),
            (half_outer, body_end),
            (bore_diameter / 2, overall_length),
            (-bore_diameter / 2, overall_length),
            (-half_outer, body_end),
        ]
    else:
        points = [
            (-half_outer, 0),
            (half_outer, 0),
            (half_outer, overall_length),
            (-half_outer, overall_length),
        ]

    if assumption.draw_physical_groove:
        points = add_groove(points, half_outer, groove_from_top)

    return RammerModel(
        key=key,
        label=label,
        role=role,
        overall_length=overall_length,
        outer_diameter=outer_diameter,
        head_length=head_length,
        groove_from_top=groove_from_top,
        switch_mark_from_top=switch_mark_from_top,
        bore_depth=bore_depth,
        bore_diameter=bore_diameter,
        nose_angle=nose_angle,
        taper_height=taper_height,
        has_taper=role == "fullDepth" and nose_angle > 0,
        points=points,
    )


def build_tool_model(
    params: ToolParams,
    assumption: AssumptionSet = BASELINE_ASSUMPTION,
    manufacturing: ManufacturingSettings | None = None,
) -> ToolModel:
    manufacturing = manufacturing or default_manufacturing_settings("in")
    validate_manufacturing_settings(manufacturing, params.a)
    head_length = params.a * HEAD_RATIO
    switch_offset = params.a * manufacturing.switch_mark_offset_diameters
    spindle = build_spindle(params, assumption)
    tip_diameter = spindle.tip_diameter
    rammer_count = max(2, int(round(params.h)))
    diameter_step = (params.d - tip_diameter) / (rammer_count - 1) if rammer_count > 1 else 0.0

    rammers: list[RammerModel] = []
    solid_length = params.b - (params.c + params.f) + head_length
    rammers.append(
        build_rammer("solid", "Solid rammer", "solid", solid_length, params.a, head_length, head_length, head_length + switch_offset, 0.0, 0.0, assumption)
    )

    full_depth_length = params.b - params.f + head_length
    rammers.append(
        build_rammer(
            "a-rammer",
            "Full-depth 'A' rammer",
            "fullDepth",
            full_depth_length,
            params.a,
            head_length,
            head_length,
            head_length + switch_offset,
            params.c,
            params.d,
            assumption,
            params.i,
        )
    )

    for step in range(1, rammer_count - 1):
        bore_depth = params.c - step * (params.c / max(rammer_count - 1, 1))
        bore_diameter = params.d - step * diameter_step
        overall_length = params.b - params.f - step * (params.c / max(rammer_count - 1, 1)) + head_length
        rammers.append(
            build_rammer(
                f"progressive-{step}",
                f"Progressive rammer {step}",
                "progressive",
                overall_length,
                params.a,
                head_length,
                head_length,
                None if step == rammer_count - 2 else head_length + switch_offset,
                bore_depth,
                bore_diameter,
                assumption,
            )
        )

    return ToolModel(
        params=params,
        assumption=assumption,
        manufacturing=manufacturing,
        head_length=head_length,
        spindle=spindle,
        rammers=rammers,
    )


def assumption_by_key(key: str) -> AssumptionSet:
    try:
        return HARNESS_ASSUMPTIONS[key]
    except KeyError as exc:
        valid = ", ".join(sorted(HARNESS_ASSUMPTIONS))
        raise KeyError(f"Unknown assumption set '{key}'. Valid keys: {valid}") from exc
