import { type ChangeEvent, useMemo, useState } from "react";
import { baselineAssumption } from "./model/assumptions";
import { fieldMeta } from "./model/fields";
import { buildToolModel, convertManufacturingSettings, convertParams, defaultManufacturingSettings, formatDimension, spindleTipUpPoints } from "./model/geometry";
import { defaultPresetKey, getPreset, presets } from "./model/presets";
import type { AssumptionSet, FieldKey, ManufacturingSettings, RammerModel, ToolModel, ToolParams, Unit } from "./model/types";

type ViewMode = "designer" | "exports";

type LayoutPart = {
  key: string;
  label: string;
  centerX: number;
  topY: number;
  kind: "spindle" | "rammer";
  rammer?: RammerModel;
};

type ExportFormat = {
  key: string;
  name: string;
  description: string;
  output: string;
  archiveName: string;
  artifactKey: "combined-dxf" | "part-dxf" | "step" | "stl" | "openscad" | "manifest";
};

const helperImages: Record<FieldKey, { src: string; alt: string }> = {
  a: { src: "/helpers/helper-a-tube-id.png", alt: "Tube I.D. helper image" },
  b: { src: "/helpers/helper-b-tube-length.png", alt: "Tube length helper image" },
  c: { src: "/helpers/helper-c-spindle-length.png", alt: "Spindle length helper image" },
  d: { src: "/helpers/helper-d-spindle-width.png", alt: "Spindle width helper image" },
  e: { src: "/helpers/helper-e-spindle-taper.png", alt: "Spindle taper helper image" },
  f: { src: "/helpers/helper-f-collar-height.png", alt: "Collar height helper image" },
  g: { src: "/helpers/helper-g-collar-taper.png", alt: "Collar taper helper image" },
  h: { src: "/helpers/helper-h-number-of-rammers.png", alt: "Number of rammers helper image" },
  i: { src: "/helpers/helper-i-a-rammer-taper.png", alt: "A rammer taper helper image" },
};

const exportFormats: ExportFormat[] = [
  {
    key: "combined-dxf",
    name: "Combined DXF",
    description: "Single drawing sheet with spindle, rammers, dimensions, hidden bores, notes, and title block.",
    output: "tooling-set-annotated.dxf",
    archiveName: "combined-dxf.zip",
    artifactKey: "combined-dxf",
  },
  {
    key: "part-dxf",
    name: "Per-part DXF",
    description: "One simple sketch/profile DXF per physical part, intended for CAD import and inspection.",
    output: "drawings/*.dxf",
    archiveName: "per-part-dxf.zip",
    artifactKey: "part-dxf",
  },
  {
    key: "step",
    name: "STEP solids",
    description: "Machining-oriented 3D solids, exported as one assembly plus one STEP per part.",
    output: "solids/*.step",
    archiveName: "step-solids.zip",
    artifactKey: "step",
  },
  {
    key: "stl",
    name: "STL preview solids",
    description: "Mesh exports for visual checks and rough 3D-printing previews, not authoritative machining geometry.",
    output: "solids/*.stl",
    archiveName: "stl-preview-solids.zip",
    artifactKey: "stl",
  },
  {
    key: "openscad",
    name: "OpenSCAD",
    description: "Parametric text export for reproducible spindle and rammer generation.",
    output: "tooling-set.scad",
    archiveName: "openscad.zip",
    artifactKey: "openscad",
  },
  {
    key: "manifest",
    name: "Manifest JSON",
    description: "Parameters, preset key, assumptions, and derived geometry for regression checks and export jobs.",
    output: "tooling-set.json",
    archiveName: "manifest-json.zip",
    artifactKey: "manifest",
  },
];

function makeDefaultParams() {
  return getPreset(defaultPresetKey).derive(0.75);
}

function unitFloor(value: number, fallbackInches: number) {
  return value > 5 ? fallbackInches * 25.4 : fallbackInches;
}

function formatDrawingNumber(value: number, unit: Unit) {
  const digits = unit === "mm" ? 2 : 3;
  const fixed = value.toFixed(digits).replace(/0+$/, "").replace(/\.$/, "");
  if (unit === "in" && fixed.startsWith("0.")) {
    return fixed.replace(/^0/, "");
  }
  return fixed;
}

function formatDrawingLength(value: number, unit: Unit) {
  return `${formatDrawingNumber(value, unit)} ${unit}`;
}

function displayPresetLabel(presetKey: string) {
  return presetKey === "custom" ? "Custom" : getPreset(presetKey).label;
}

function presetSheetTitle(presetKey: string, params: ToolParams, unit: Unit, assumption?: AssumptionSet) {
  const label = displayPresetLabel(presetKey);
  const suffix = assumption && assumption.key !== "baseline" ? ` - ${assumption.label}` : "";
  const size = unit === "in" ? `${formatDrawingNumber(params.a, unit)}\"` : `${formatDrawingNumber(params.a, unit)} mm`;
  return `${size} ${label}${suffix}`;
}

function pathData(points: [number, number][], centerX: number, topY: number) {
  return points.map(([x, y], index) => `${index === 0 ? "M" : "L"} ${centerX + x} ${topY + y}`).join(" ") + " Z";
}

function spindlePathData(model: ToolModel, centerX: number, topY: number) {
  return pathData(spindleTipUpPoints(model.spindle), centerX, topY);
}

function computeLayout(model: ToolModel) {
  const a = model.params.a;
  const topY = Math.max(a * 2.65, unitFloor(a, 1.7));
  const leftX = Math.max(a * 4.2, unitFloor(a, 2.2));
  const spacing = Math.max(a * 5.4, unitFloor(a, 2.9));
  const rightMargin = Math.max(a * 2.6, unitFloor(a, 1.6));
  const maxRammerLength = Math.max(...model.rammers.map((rammer) => rammer.overallLength));
  const solid = model.rammers[0];
  const spindleGapBelowSolid = Math.max(a * 0.35, unitFloor(a, 0.25));
  const spindleExtraBelowLongest = Math.max(a * 0.8, unitFloor(a, 0.45));
  const spindleTopY = Math.max(
    topY + solid.overallLength + spindleGapBelowSolid,
    topY + maxRammerLength - model.spindle.totalLength + spindleExtraBelowLongest,
  );

  const parts: LayoutPart[] = [
    { key: "spindle", label: "Spindle", centerX: leftX, topY: spindleTopY, kind: "spindle" },
  ];

  model.rammers.forEach((rammer, index) => {
    parts.push({
      key: rammer.key,
      label: rammer.label,
      centerX: leftX + index * spacing,
      topY,
      kind: "rammer",
      rammer,
    });
  });

  const lastX = leftX + (model.rammers.length - 1) * spacing;
  const width = lastX + rightMargin;
  const height = Math.max(spindleTopY + model.spindle.totalLength, topY + maxRammerLength) + Math.max(a * 1.65, unitFloor(a, 0.95));
  return { parts, topY, width, height };
}

function DimensionHorizontal({ x1, x2, y, label }: { x1: number; x2: number; y: number; label: string }) {
  const tick = Math.max(Math.abs(x2 - x1) * 0.12, 0.06);
  return (
    <g className="rts-dim">
      <line x1={x1} y1={y} x2={x2} y2={y} />
      <line x1={x1} y1={y - tick} x2={x1} y2={y + tick} />
      <line x1={x2} y1={y - tick} x2={x2} y2={y + tick} />
      <text x={(x1 + x2) / 2} y={y - tick * 0.5} textAnchor="middle" className="rts-dim-text">
        {label}
      </text>
    </g>
  );
}

function DimensionVertical({ x, y1, y2, label, side = "right" }: { x: number; y1: number; y2: number; label: string; side?: "left" | "right" }) {
  const tick = Math.max(Math.abs(y2 - y1) * 0.025, 0.08);
  const offset = side === "left" ? -tick * 1.25 : tick * 1.25;
  return (
    <g className="rts-dim">
      <line x1={x} y1={y1} x2={x} y2={y2} />
      <line x1={x - tick} y1={y1} x2={x + tick} y2={y1} />
      <line x1={x - tick} y1={y2} x2={x + tick} y2={y2} />
      <text x={x + offset} y={(y1 + y2) / 2} className="rts-dim-text" transform={`rotate(-90 ${x + offset} ${(y1 + y2) / 2})`}>
        {label}
      </text>
    </g>
  );
}

function Leader({ x1, y1, x2, y2, label, anchor = "start" }: { x1: number; y1: number; x2: number; y2: number; label: string; anchor?: "start" | "end" }) {
  const textX = anchor === "end" ? x2 - 0.04 : x2 + 0.04;
  return (
    <g className="rts-leader">
      <line x1={x1} y1={y1} x2={x2} y2={y2} />
      <text x={textX} y={y2 - 0.03} textAnchor={anchor} className="rts-callout-text">
        {label}
      </text>
    </g>
  );
}

function HiddenBore({ rammer, centerX, topY }: { rammer: RammerModel; centerX: number; topY: number }) {
  if (rammer.boreDepth <= 0 || rammer.boreDiameter <= 0) {
    return null;
  }
  const half = rammer.boreDiameter / 2;
  const boreTop = topY + rammer.overallLength - rammer.boreDepth;
  const boreBottom = topY + rammer.overallLength;
  return (
    <g className="rts-hidden">
      <line x1={centerX - half} y1={boreTop} x2={centerX - half} y2={boreBottom} />
      <line x1={centerX + half} y1={boreTop} x2={centerX + half} y2={boreBottom} />
      <line x1={centerX - half} y1={boreTop} x2={centerX + half} y2={boreTop} />
    </g>
  );
}

function RammerShape({ rammer, centerX, topY }: { rammer: RammerModel; centerX: number; topY: number }) {
  return (
    <g>
      <path d={pathData(rammer.points, centerX, topY)} className="rts-profile" />
      <HiddenBore rammer={rammer} centerX={centerX} topY={topY} />
      <line x1={centerX} y1={topY - rammer.outerDiameter * 0.35} x2={centerX} y2={topY + rammer.overallLength + rammer.outerDiameter * 0.35} className="rts-centerline" />
      <line x1={centerX - rammer.outerDiameter / 2} y1={topY + rammer.grooveFromTop} x2={centerX + rammer.outerDiameter / 2} y2={topY + rammer.grooveFromTop} className="rts-mark" />
      {rammer.switchMarkFromTop !== null ? (
        <line x1={centerX - rammer.outerDiameter / 2} y1={topY + rammer.switchMarkFromTop} x2={centerX + rammer.outerDiameter / 2} y2={topY + rammer.switchMarkFromTop} className="rts-switch-mark" />
      ) : null}
    </g>
  );
}

function ToolingSheet({
  model,
  presetKey,
  unit,
  showDimensions,
  assumption,
}: {
  model: ToolModel;
  presetKey: string;
  unit: Unit;
  showDimensions: boolean;
  assumption?: AssumptionSet;
}) {
  const layout = computeLayout(model);
  const a = model.params.a;
  const title = presetSheetTitle(presetKey, model.params, unit, assumption);
  const dimLift = Math.max(a * 0.75, unitFloor(a, 0.36));
  const labelDrop = Math.max(a * 0.42, unitFloor(a, 0.24));

  return (
    <svg className="tooling-svg" viewBox={`0 0 ${layout.width} ${layout.height}`} role="img" aria-label={title} preserveAspectRatio="xMidYMin meet">
      <rect x="0" y="0" width={layout.width} height={layout.height} className="rts-sheet-bg" />
      <text x={layout.width / 2} y={Math.max(a * 0.78, unitFloor(a, 0.55))} textAnchor="middle" className="rts-sheet-title">
        {title}
      </text>

      {layout.parts.map((part) => {
        if (part.kind === "spindle") {
          const spindle = model.spindle;
          const tipY = part.topY;
          const rootY = part.topY + spindle.spindleLength;
          const collarTopY = part.topY + spindle.totalLength - spindle.collarHeight;
          const collarTaperStartY = part.topY + spindle.totalLength - Math.max(spindle.collarHeight - spindle.collarRise, 0);
          const collarBottomY = part.topY + spindle.totalLength;
          return (
            <g key={part.key}>
              <path d={spindlePathData(model, part.centerX, part.topY)} className="rts-profile" />
              <line x1={part.centerX} y1={part.topY - a * 0.35} x2={part.centerX} y2={collarBottomY + a * 0.35} className="rts-centerline" />
              {showDimensions ? (
                <>
                  <DimensionVertical x={part.centerX + a * 0.95} y1={tipY} y2={rootY} label={formatDrawingLength(spindle.spindleLength, unit)} />
                  <DimensionVertical x={part.centerX + a * 1.35} y1={tipY} y2={collarBottomY} label={formatDrawingLength(spindle.totalLength, unit)} />
                  <DimensionVertical x={part.centerX - a * 1.05} y1={collarTopY} y2={collarBottomY} label={formatDrawingLength(spindle.collarHeight, unit)} side="left" />
                  {spindle.collarRise > 0 ? (
                    <DimensionVertical x={part.centerX - a * 1.45} y1={collarTaperStartY} y2={collarTopY} label={formatDrawingLength(spindle.collarRise, unit)} side="left" />
                  ) : null}
                  <Leader x1={part.centerX + spindle.tipDiameter / 2} y1={tipY} x2={part.centerX - a * 1.65} y2={tipY + a * 0.3} label={`tip ${formatDrawingLength(spindle.tipDiameter, unit)}`} anchor="end" />
                  <Leader x1={part.centerX + spindle.rootDiameter / 2} y1={rootY} x2={part.centerX - a * 1.6} y2={rootY + a * 0.12} label={`root ${formatDrawingLength(spindle.rootDiameter, unit)}`} anchor="end" />
                  <Leader x1={part.centerX + spindle.tubeDiameter / 2} y1={collarBottomY - spindle.collarHeight * 0.5} x2={part.centerX - a * 1.65} y2={collarBottomY - a * 0.35} label={`collar ${formatDrawingLength(spindle.tubeDiameter, unit)}`} anchor="end" />
                  <Leader x1={part.centerX + spindle.rootDiameter / 2} y1={rootY + a * 0.15} x2={part.centerX + a * 1.25} y2={rootY + a * 0.45} label={`${formatDrawingNumber(model.params.e, unit)}° side`} />
                  <Leader x1={part.centerX + spindle.tubeDiameter / 2} y1={collarTopY} x2={part.centerX + a * 1.35} y2={collarBottomY - a * 0.12} label={`${formatDrawingNumber(model.params.g, unit)}° collar`} />
                </>
              ) : null}
              <text x={part.centerX} y={collarBottomY + labelDrop} textAnchor="middle" className="rts-label">
                Spindle
              </text>
            </g>
          );
        }

        const rammer = part.rammer;
        if (!rammer) {
          return null;
        }
        const topY = part.topY;
        const bottomY = part.topY + rammer.overallLength;
        const totalDimX = part.centerX + rammer.outerDiameter * 1.75;
        const headDimX = part.centerX + rammer.outerDiameter * 1.22;
        const boreDimX = part.centerX + rammer.outerDiameter * 2.15;
        return (
          <g key={part.key}>
            <RammerShape rammer={rammer} centerX={part.centerX} topY={part.topY} />
            {showDimensions ? (
              <>
                <DimensionHorizontal x1={part.centerX - rammer.outerDiameter / 2} x2={part.centerX + rammer.outerDiameter / 2} y={topY - dimLift} label={formatDrawingLength(rammer.outerDiameter, unit)} />
                <DimensionVertical x={headDimX} y1={topY} y2={topY + rammer.headLength} label={formatDrawingLength(rammer.headLength, unit)} />
                <DimensionVertical x={totalDimX} y1={topY} y2={bottomY} label={formatDrawingLength(rammer.overallLength, unit)} />
                {rammer.boreDepth > 0 && rammer.boreDiameter > 0 ? (
                  <>
                    <DimensionVertical x={boreDimX} y1={bottomY - rammer.boreDepth} y2={bottomY} label={formatDrawingLength(rammer.boreDepth, unit)} />
                    <DimensionHorizontal x1={part.centerX - rammer.boreDiameter / 2} x2={part.centerX + rammer.boreDiameter / 2} y={bottomY + dimLift * 0.7} label={formatDrawingLength(rammer.boreDiameter, unit)} />
                  </>
                ) : null}
                {rammer.hasTaper ? (
                  <Leader x1={part.centerX + rammer.boreDiameter / 2} y1={bottomY} x2={part.centerX + rammer.outerDiameter * 1.18} y2={bottomY - Math.max(rammer.taperHeight, a * 0.25)} label={`${formatDrawingNumber(rammer.noseAngle, unit)}°`} />
                ) : null}
              </>
            ) : null}
            <text x={part.centerX} y={bottomY + labelDrop} textAnchor="middle" className="rts-label">
              {rammer.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function requestExportArchive(payload: {
  artifactKey: "review" | "combined-dxf" | "part-dxf" | "step" | "stl" | "openscad" | "manifest";
  archiveName: string;
  presetKey: string;
  unit: Unit;
  params: ToolParams;
  assumptionKey: string;
  manufacturing: ManufacturingSettings;
}) {
  const response = await fetch("/api/export", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("content-disposition") ?? "";
  const match = /filename=\"?([^\";]+)\"?/i.exec(contentDisposition);
  downloadBlob(match?.[1] ?? payload.archiveName, blob);
}

function DesignerView({
  presetKey,
  setPresetKey,
  params,
  setParams,
  unit,
  setUnit,
  manufacturing,
  setManufacturing,
}: {
  presetKey: string;
  setPresetKey: (value: string) => void;
  params: ToolParams;
  setParams: (value: ToolParams) => void;
  unit: Unit;
  setUnit: (value: Unit) => void;
  manufacturing: ManufacturingSettings;
  setManufacturing: (value: ManufacturingSettings) => void;
}) {
  const [showDimensions, setShowDimensions] = useState(true);
  const [activeHelper, setActiveHelper] = useState<{ key: FieldKey; top: number; left: number } | null>(null);
  const assumption = baselineAssumption;
  const model = useMemo(() => buildToolModel(params, assumption, manufacturing), [params, assumption, manufacturing]);
  const isCustom = presetKey === "custom";

  const setField = (key: FieldKey, value: number) => {
    if (!isCustom && key !== "a") {
      return;
    }
    if (!isCustom && key === "a") {
      setParams(getPreset(presetKey).derive(value));
      return;
    }
    setParams({ ...params, [key]: key === "h" ? Math.round(value) : value });
  };

  const setManufacturingField = (key: keyof ManufacturingSettings, value: number) => {
    let next = Number.isFinite(value) ? Math.max(value, 0) : 0;
    if (key === "minimumDiametralClearance") {
      next = Math.min(Math.max(next, unit === "mm" ? 0.001 : 0.0001), params.a * 0.1);
    } else if (key === "generalTolerance") {
      next = Math.min(next, params.a * 0.05);
    } else if (key === "switchMarkOffsetDiameters") {
      next = Math.max(next, 0.1);
    }
    setManufacturing({ ...manufacturing, [key]: next });
  };

  const showHelper = (key: FieldKey, element: HTMLLabelElement) => {
    const rect = element.getBoundingClientRect();
    setActiveHelper({
      key,
      top: rect.top + rect.height / 2,
      left: Math.max(12, rect.left - 170),
    });
  };

  return (
    <div className="legacy-layout">
      <main className="drawing-area">
        <div className="sheet-strip">
          <div>
            <p className="sheet-kicker">{presetKey === "custom" ? "Custom tooling" : getPreset(presetKey).label}</p>
            <h2>{formatDimension(params.a, unit)} tooling set</h2>
          </div>
          <div className="sheet-meta">
            <span>{params.h} rammers</span>
            <span>Finished dimensions</span>
          </div>
        </div>
        <ToolingSheet model={model} presetKey={presetKey} unit={unit} showDimensions={showDimensions} />
      </main>

      <aside className="legacy-controls">
        <label className="field compact-field">
          <span>Tooling type</span>
          <select
            value={presetKey}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              const next = event.target.value;
              setPresetKey(next);
              if (next !== "custom") {
                setParams(getPreset(next).derive(params.a));
              }
            }}
          >
            <option value="custom">Custom</option>
            {presets.map((preset) => (
              <option key={preset.key} value={preset.key}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>

        <div className="control-block">
          <span className="control-label">Units</span>
          <div className="toggle-row">
            <button
              className={unit === "in" ? "button active" : "button"}
              onClick={() => {
                if (unit !== "in") {
                  setParams(convertParams(params, "in"));
                  setManufacturing(convertManufacturingSettings(manufacturing, "in"));
                  setUnit("in");
                }
              }}
            >
              Inches
            </button>
            <button
              className={unit === "mm" ? "button active" : "button"}
              onClick={() => {
                if (unit !== "mm") {
                  setParams(convertParams(params, "mm"));
                  setManufacturing(convertManufacturingSettings(manufacturing, "mm"));
                  setUnit("mm");
                }
              }}
            >
              Millimeters
            </button>
          </div>
        </div>

        <div className="control-block">
          <span className="control-label">Drawing</span>
          <button className="button" onClick={() => setShowDimensions(!showDimensions)}>
            {showDimensions ? "Hide dimensions" : "Show dimensions"}
          </button>
        </div>

        <div className="field-list">
          {fieldMeta.map((field) => (
            <label
              key={field.key}
              className="field compact-field helper-field"
              onMouseEnter={(event) => showHelper(field.key, event.currentTarget)}
              onFocusCapture={(event) => showHelper(field.key, event.currentTarget)}
              onMouseLeave={() => setActiveHelper((current) => (current?.key === field.key ? null : current))}
              onBlurCapture={(event) => {
                const nextTarget = event.relatedTarget;
                if (!nextTarget || !event.currentTarget.contains(nextTarget as Node)) {
                  setActiveHelper((current) => (current?.key === field.key ? null : current));
                }
              }}
            >
              <span>
                {field.label}
                <small>{field.hint}</small>
              </span>
              <input
                type="number"
                min={0}
                step={field.key === "h" ? 1 : 0.01}
                value={params[field.key]}
                disabled={!isCustom && field.key !== "a"}
                onChange={(event: ChangeEvent<HTMLInputElement>) => setField(field.key, Number(event.target.value))}
              />
            </label>
          ))}
        </div>

        <details className="manufacturing-settings">
          <summary>Manufacturing tolerances</summary>
          <p className="settings-help">Bores use a positive allowance and spindle diameters a negative allowance, preserving at least the selected diametral clearance.</p>
          {([
            ["generalTolerance", "General ± tolerance"],
            ["spindleMinusTolerance", "Spindle OD minus tolerance"],
            ["borePlusTolerance", "Bore plus tolerance"],
            ["minimumDiametralClearance", "Minimum diametral clearance"],
            ["switchMarkOffsetDiameters", "Switch mark offset (tube I.D.s)"],
            ["spindleFinishRa", `Spindle finish Ra (${unit === "mm" ? "µm" : "µin"})`],
            ["rammerOdFinishRa", `Rammer OD finish Ra (${unit === "mm" ? "µm" : "µin"})`],
            ["rammerBoreFinishRa", `Rammer bore finish Ra (${unit === "mm" ? "µm" : "µin"})`],
          ] as [keyof ManufacturingSettings, string][]).map(([key, label]) => (
            <label className="field compact-field" key={key}>
              <span>{label}</span>
              <input
                type="number"
                min={key === "minimumDiametralClearance" || key === "switchMarkOffsetDiameters" ? 0.0001 : 0}
                max={key === "minimumDiametralClearance" ? params.a * 0.1 : key === "generalTolerance" ? params.a * 0.05 : undefined}
                step={key.includes("Finish") ? 1 : 0.001}
                value={manufacturing[key]}
                onChange={(event) => setManufacturingField(key, Number(event.target.value))}
              />
            </label>
          ))}
          <p className="clearance-check">Worst-case diametral clearance: {formatDrawingLength(manufacturing.minimumDiametralClearance, unit)}</p>
        </details>
      </aside>
      {activeHelper ? (
        <div className="helper-layer" aria-hidden="true">
          <div className="helper-popover" style={{ top: activeHelper.top, left: activeHelper.left }}>
            <img src={helperImages[activeHelper.key].src} alt={helperImages[activeHelper.key].alt} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ExportsView({ presetKey, params, unit, manufacturing }: { presetKey: string; params: ToolParams; unit: Unit; manufacturing: ManufacturingSettings }) {
  const model = useMemo(() => buildToolModel(params, baselineAssumption, manufacturing), [params, manufacturing]);

  const downloadArtifact = async (
    artifactKey: "review" | "combined-dxf" | "part-dxf" | "step" | "stl" | "openscad" | "manifest",
    archiveName: string,
  ) => {
    await requestExportArchive({
      artifactKey,
      archiveName,
      presetKey,
      unit,
      params: model.params,
      assumptionKey: model.assumption.key,
      manufacturing,
    });
  };

  return (
    <div className="exports-layout">
      <section className="export-main">
        <div className="export-header-card">
          <p className="sheet-kicker">Export center</p>
          <h2>
            {displayPresetLabel(presetKey)} — {formatDimension(params.a, unit)}
          </h2>
          <p>Generate export archives from the Python tooling pipeline.</p>
          <div className="export-actions">
            <button className="button active" onClick={() => downloadArtifact("review", "review-bundle.zip")}>
              Download review ZIP
            </button>
            <button className="button" onClick={() => downloadArtifact("manifest", "manifest-json.zip")}>
              Manifest ZIP
            </button>
            <button className="button" onClick={() => downloadArtifact("openscad", "openscad.zip")}>
              OpenSCAD ZIP
            </button>
          </div>
        </div>

        <div className="export-preview-card">
          <h3>Sheet preview</h3>
          <ToolingSheet model={model} presetKey={presetKey} unit={unit} showDimensions={false} />
        </div>
      </section>

      <aside className="export-format-panel">
        <h3>Formats</h3>
        <div className="format-list">
          {exportFormats.map((format) => (
            <article key={format.key} className="format-card">
              <div>
                <strong>{format.name}</strong>
                <span>{format.output}</span>
              </div>
              <p>{format.description}</p>
              <button className="button" onClick={() => downloadArtifact(format.artifactKey, format.archiveName)}>
                Download ZIP
              </button>
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}

function App() {
  const [view, setView] = useState<ViewMode>("designer");
  const [presetKey, setPresetKey] = useState(defaultPresetKey);
  const [unit, setUnit] = useState<Unit>("in");
  const [params, setParams] = useState<ToolParams>(makeDefaultParams());
  const [manufacturing, setManufacturing] = useState<ManufacturingSettings>(() => defaultManufacturingSettings("in"));

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Rocket Tooling Designer</p>
          <h1>Parametric rocket tooling drawings</h1>
          <p className="lede">Legacy-compatible spindle and rammer tooling, based on the original Rocket Tool Sketcher formulas.</p>
        </div>
        <div className="hero-actions">
          <button className={view === "designer" ? "nav-button active" : "nav-button"} onClick={() => setView("designer")}>
            Designer
          </button>
          <button className={view === "exports" ? "nav-button active" : "nav-button"} onClick={() => setView("exports")}>
            Exports
          </button>
        </div>
      </header>

      {view === "designer" ? (
        <DesignerView presetKey={presetKey} setPresetKey={setPresetKey} params={params} setParams={setParams} unit={unit} setUnit={setUnit} manufacturing={manufacturing} setManufacturing={setManufacturing} />
      ) : (
        <ExportsView presetKey={presetKey} params={params} unit={unit} manufacturing={manufacturing} />
      )}
    </div>
  );
}

export default App;
