import type { AssumptionSet } from "./types";

export const baselineAssumption: AssumptionSet = {
  key: "baseline",
  label: "Baseline",
  notes: "E from axis, G from shoulder face, I from face, groove drawn as a real shallow V-mark.",
  angleE: "from_axis",
  angleG: "from_shoulder_face",
  angleI: "from_face",
  grooveMode: "v-groove",
  drawPhysicalGroove: true,
};

export const harnessAssumptions: AssumptionSet[] = [
  baselineAssumption,
  {
    key: "e-included",
    label: "E as included angle",
    notes: "Halves the per-side spindle taper to test a misread drafting convention.",
    angleE: "included_angle",
    angleG: "from_shoulder_face",
    angleI: "from_face",
    grooveMode: "v-groove",
    drawPhysicalGroove: true,
  },
  {
    key: "g-from-axis",
    label: "G from axis",
    notes: "Treats collar taper as an axial taper instead of a shoulder-face angle.",
    angleE: "from_axis",
    angleG: "from_axis",
    angleI: "from_face",
    grooveMode: "v-groove",
    drawPhysicalGroove: true,
  },
  {
    key: "i-from-axis",
    label: "I from axis",
    notes: "Tests whether the first rammer taper is measured from the axis rather than the lower face.",
    angleE: "from_axis",
    angleG: "from_shoulder_face",
    angleI: "from_axis",
    grooveMode: "v-groove",
    drawPhysicalGroove: true,
  },
  {
    key: "groove-line-only",
    label: "Groove as scribed line",
    notes: "Suppresses any physical groove notch and keeps only a drawn mark.",
    angleE: "from_axis",
    angleG: "from_shoulder_face",
    angleI: "from_face",
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
];
