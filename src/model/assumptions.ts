import type { AssumptionSet } from "./types";

export const baselineAssumption: AssumptionSet = {
  key: "baseline",
  label: "Baseline",
  notes: "Legacy-compatible angle conventions and scribed do-not-pass marks.",
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
    notes: "Test spindle taper if E were interpreted as an included angle.",
    angleE: "included_angle",
    angleG: "from_shoulder_face",
    angleI: "from_face",
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
  {
    key: "g-from-axis",
    label: "G from axis",
    notes: "Test collar taper if G were measured from the spindle axis.",
    angleE: "from_axis",
    angleG: "from_axis",
    angleI: "from_face",
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
  {
    key: "i-from-axis",
    label: "I from axis",
    notes: "Test A-rammer taper if I were measured from the rammer axis.",
    angleE: "from_axis",
    angleG: "from_shoulder_face",
    angleI: "from_axis",
    grooveMode: "line",
    drawPhysicalGroove: false,
  },
  {
    key: "groove-v-groove",
    label: "Physical V-groove",
    notes: "Test do-not-pass marks as machined V-grooves instead of scribed lines.",
    angleE: "from_axis",
    angleG: "from_shoulder_face",
    angleI: "from_face",
    grooveMode: "v-groove",
    drawPhysicalGroove: true,
  },
];
