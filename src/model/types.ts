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

export type ManufacturingSettings = {
  generalTolerance: number;
  spindleMinusTolerance: number;
  borePlusTolerance: number;
  minimumDiametralClearance: number;
  switchMarkOffsetDiameters: number;
  spindleFinishRa: number;
  rammerOdFinishRa: number;
  rammerBoreFinishRa: number;
};

export type SpindleBaseSettings = {
  enabled: boolean;
  shape: "round" | "square";
  size: number;
  height: number;
  extensionDiameter: number;
  extensionLength: number;
  fastenerThread: "#10-24" | "1/4-20" | "5/16-18" | "3/8-16";
  clearanceHoleDiameter: number;
  counterboreDiameter: number;
  counterboreDepth: number;
  tapDepth: number;
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
  collarRise: number;
  base: SpindleBaseSettings;
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
  switchMarkFromTop: number | null;
  boreDepth: number;
  boreDiameter: number;
  noseAngle: number;
  taperHeight: number;
  hasTaper: boolean;
  points: [number, number][];
};

export type ToolModel = {
  params: ToolParams;
  assumption: AssumptionSet;
  manufacturing: ManufacturingSettings;
  spindleBase: SpindleBaseSettings;
  headLength: number;
  spindle: SpindleModel;
  rammers: RammerModel[];
};
