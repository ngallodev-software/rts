import type { AssumptionSet } from "./types";

export const baselineAssumption: AssumptionSet = {
  key: "baseline",
  label: "Baseline",
  notes: "E from axis, G from shoulder face, I from face, do-not-pass mark drawn as a scribed line by default.",
  angleE: "from_axis",
  angleG: "from_shoulder_face",
  angleI: "from_face",
  grooveMode: "line",
  drawPhysicalGroove: false,
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
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
  {
    key: "g-from-axis",
    label: "G from axis",
    notes: "Treats collar taper as an axial taper instead of a shoulder-face angle.",
    angleE: "from_axis",
    angleG: "from_axis",
    angleI: "from_face",
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
  {
    key: "i-from-axis",
    label: "I from axis",
    notes: "Tests whether the first rammer taper is measured from the axis rather than the working face.",
    angleE: "from_axis",
    angleG: "from_shoulder_face",
    angleI: "from_axis",
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
  {
    key: "groove-v-groove",
    label: "Physical V-groove",
    notes: "Draws the do-not-pass mark as a shallow V-groove to test the older physical-groove interpretation.",
    angleE: "from_axis",
    angleG: "from_shoulder_face",
    angleI: "from_face",
    grooveMode: "v-groove",
    drawPhysicalGroove: true,
  },
];
