import { baselineAssumption } from "./assumptions";
import type { AssumptionSet, RammerModel, SpindleModel, ToolModel, ToolParams, Unit } from "./types";

export const MM_PER_INCH = 25.4;
export const HEAD_RATIO = 1.5;

export function round(value: number, digits: number) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

export function convertParams(params: ToolParams, nextUnit: Unit): ToolParams {
  const factor = nextUnit === "mm" ? MM_PER_INCH : 1 / MM_PER_INCH;
  const digits = nextUnit === "mm" ? 2 : 4;
  return {
    ...params,
    a: round(params.a * factor, digits),
    b: round(params.b * factor, digits),
    c: round(params.c * factor, digits),
    d: round(params.d * factor, digits),
    f: round(params.f * factor, digits),
  };
}

function normalizeAngle(angle: number, mode: AssumptionSet["angleE" | "angleG" | "angleI"]) {
  switch (mode) {
    case "included_angle":
      return angle / 2;
    default:
      return angle;
  }
}

function tanDeg(value: number) {
  return Math.tan((value * Math.PI) / 180);
}

function spindleTipDiameter(params: ToolParams, assumption: AssumptionSet) {
  const angle = normalizeAngle(params.e, assumption.angleE);
  return Math.max(params.d - 2 * params.c * tanDeg(angle), 0);
}

function collarRise(params: ToolParams, assumption: AssumptionSet) {
  if (params.g === 0) {
    return 0;
  }
  const angle = normalizeAngle(params.g, assumption.angleG);
  if (assumption.angleG === "from_axis") {
    return ((params.a - params.d) / 2) / Math.max(tanDeg(90 - angle), 0.0001);
  }
  return ((params.a - params.d) / 2) * tanDeg(angle);
}

function buildSpindle(params: ToolParams, assumption: AssumptionSet): SpindleModel {
  const d2 = spindleTipDiameter(params, assumption);
  const rise = collarRise(params, assumption);
  const shoulderY = -(params.f - rise);

  return {
    tubeDiameter: params.a,
    collarHeight: params.f,
    spindleLength: params.c,
    rootDiameter: params.d,
    tipDiameter: d2,
    totalLength: params.c + params.f,
    points: [
      [params.a / 2, 0],
      [params.a / 2, shoulderY],
      [params.d / 2, -params.f],
      [d2 / 2, -(params.f + params.c)],
      [-d2 / 2, -(params.f + params.c)],
      [-params.d / 2, -params.f],
      [-params.a / 2, shoulderY],
      [-params.a / 2, 0],
    ],
  };
}

function firstRammerNoseStartX(params: ToolParams, assumption: AssumptionSet) {
  const noseAngle = normalizeAngle(params.i, assumption.angleI);
  if (params.i === 0 || noseAngle === 0) {
    return params.a / 2;
  }

  if (assumption.angleI === "from_axis") {
    const run = (params.a - params.d) / 2;
    const rise = run * tanDeg(noseAngle);
    return Math.max((params.a / 2) - rise, params.d / 2);
  }

  const run = (params.a - params.d) / 2;
  const rise = run / Math.max(tanDeg(noseAngle), 0.0001);
  return Math.max((params.a / 2) - rise, params.d / 2);
}

function addGroove(points: [number, number][], outerRadius: number, grooveY: number) {
  return points.flatMap(([x, y], index) => {
    if (index !== 2) {
      return [[x, y] as [number, number]];
    }

    const inset = outerRadius * 0.06;
    const grooveHeight = outerRadius * 0.04;
    return [
      [x, grooveY + grooveHeight] as [number, number],
      [x - inset, grooveY] as [number, number],
      [x, grooveY - grooveHeight] as [number, number],
      [x, y] as [number, number],
    ];
  });
}

function buildRammer(
  key: string,
  label: string,
  role: RammerModel["role"],
  overallLength: number,
  outerDiameter: number,
  headLength: number,
  grooveFromTop: number,
  boreDepth: number,
  boreDiameter: number,
  assumption: AssumptionSet,
  noseAngle = 0,
): RammerModel {
  const halfOuter = outerDiameter / 2;
  const grooveY = grooveFromTop;
  let points: [number, number][];

  if (role === "fullDepth" && noseAngle > 0) {
    const startY = firstRammerNoseStartX(
      { a: outerDiameter, b: 0, c: 0, d: boreDiameter, e: 0, f: 0, g: 0, h: 0, i: noseAngle },
      assumption,
    );
    points = [
      [-halfOuter, 0],
      [halfOuter, 0],
      [halfOuter, overallLength - startY],
      [boreDiameter / 2, overallLength],
      [-boreDiameter / 2, overallLength],
      [-halfOuter, overallLength - startY],
    ];
  } else {
    points = [
      [-halfOuter, 0],
      [halfOuter, 0],
      [halfOuter, overallLength],
      [-halfOuter, overallLength],
    ];
  }

  if (assumption.drawPhysicalGroove) {
    points = addGroove(points, halfOuter, grooveY);
  }

  return {
    key,
    label,
    role,
    overallLength,
    outerDiameter,
    headLength,
    grooveFromTop,
    boreDepth,
    boreDiameter,
    noseAngle,
    hasTaper: role === "fullDepth" && noseAngle > 0,
    points,
  };
}

export function buildToolModel(params: ToolParams, assumption: AssumptionSet = baselineAssumption): ToolModel {
  const headLength = params.a * HEAD_RATIO;
  const spindle = buildSpindle(params, assumption);
  const d2 = spindle.tipDiameter;
  const h = Math.max(2, Math.round(params.h));
  const hci = h > 1 ? (params.d - d2) / (h - 1) : 0;

  const rammers: RammerModel[] = [];

  const solidLength = params.b - (params.c + params.f) + headLength;
  rammers.push(
    buildRammer("solid", "Solid rammer", "solid", solidLength, params.a, headLength, headLength, 0, 0, assumption),
  );

  const fullDepthLength = params.b - params.f + headLength;
  rammers.push(
    buildRammer(
      "a-rammer",
      "Full-depth 'A' rammer",
      "fullDepth",
      fullDepthLength,
      params.a,
      headLength,
      headLength,
      params.c,
      params.d,
      assumption,
      params.i,
    ),
  );

  for (let step = 1; step <= h - 2; step += 1) {
    const boreDepth = params.c - step * (params.c / Math.max(h - 1, 1));
    const boreDiameter = params.d - step * hci;
    const overallLength = params.b - params.f - step * (params.c / Math.max(h - 1, 1)) + headLength;

    rammers.push(
      buildRammer(
        `progressive-${step}`,
        `Progressive rammer ${step}`,
        "progressive",
        overallLength,
        params.a,
        headLength,
        headLength,
        boreDepth,
        boreDiameter,
        assumption,
      ),
    );
  }

  return { params, assumption, headLength, spindle, rammers };
}

export function formatDimension(value: number, unit: Unit) {
  return `${round(value, unit === "mm" ? 2 : 3)} ${unit}`;
}
