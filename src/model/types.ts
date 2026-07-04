export type Unit = "in" | "mm";

export type ToolParams = {
  a: number;
  b: number;
  c: number;
  d: number;
  e: number;
  f: number;
  g: number;
  h: number;
  i: number;
};

export type FieldKey = keyof ToolParams;

export type FieldMeta = {
  key: FieldKey;
  code: string;
  label: string;
  hint: string;
};

export type PresetDefinition = {
  key: string;
  label: string;
  notes?: string;
  derive: (tubeId: number) => ToolParams;
};

export type AngleConvention = "from_axis" | "from_face" | "from_shoulder_face" | "included_angle";

export type AssumptionSet = {
  key: string;
  label: string;
  notes: string;
  angleE: AngleConvention;
  angleG: AngleConvention;
  angleI: AngleConvention;
  grooveMode: "line" | "v-groove";
  drawPhysicalGroove: boolean;
};

export type SpindleModel = {
  tubeDiameter: number;
  collarHeight: number;
  spindleLength: number;
  rootDiameter: number;
  tipDiameter: number;
  totalLength: number;
  points: [number, number][];
};

export type RammerModel = {
  key: string;
  label: string;
  role: "solid" | "fullDepth" | "progressive";
  overallLength: number;
  outerDiameter: number;
  headLength: number;
  grooveFromTop: number;
  boreDepth: number;
  boreDiameter: number;
  noseAngle: number;
  hasTaper: boolean;
  points: [number, number][];
};

export type ToolModel = {
  params: ToolParams;
  assumption: AssumptionSet;
  headLength: number;
  spindle: SpindleModel;
  rammers: RammerModel[];
};
