import { type ChangeEvent, useMemo, useState } from "react";
import { baselineAssumption, harnessAssumptions } from "./model/assumptions";
import { fieldMeta } from "./model/fields";
import { buildToolModel, convertParams, formatDimension, spindleTipUpPoints } from "./model/geometry";
import { defaultPresetKey, getPreset, presets } from "./model/presets";
import type { AssumptionSet, RammerModel, ToolModel, ToolParams, Unit } from "./model/types";

type ViewMode = "designer" | "harness";

type LayoutPart = {
  key: string;
  label: string;
  centerX: number;
  topY: number;
  kind: "spindle" | "rammer";
  rammer?: RammerModel;
};

const helperImages: Record<keyof ToolParams, { src: string; alt: string }> = {
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

function makeDefaultParams() {
  return getPreset(defaultPresetKey).derive(0.75);
}

function formatDrawingNumber(value: number, unit: Unit) {
  const digits = unit === "mm" ? 2 : 3;
  const fixed = value.toFixed(digits).replace(/0+$/, "").replace(/\.$/, "");
  if (unit === "in" && fixed.startsWith("0.")) {
    return fixed.replace(/^0/, "");
  }
  return fixed;
}

function presetSheetTitle(presetKey: string, params: ToolParams, unit: Unit, assumption?: AssumptionSet) {
  const label = presetKey === "custom" ? "Custom" : getPreset(presetKey).label;
  const suffix = assumption && assumption.key !== "baseline" ? ` - ${assumption.label}` : "";
  const size = unit === "in" ? `${formatDrawingNumber(params.a, unit)}\"` : `${formatDrawingNumber(params.a, unit)} mm`;
  return `${size} ${label}${suffix}`;
}

function pathData(points: [number, number][], centerX: number, topY: number) {
  return points
    .map(([x, y], index) => `${index === 0 ? "M" : "L"} ${centerX + x} ${topY + y}`)
    .join(" ") + " Z";
}

function spindlePathData(model: ToolModel, centerX: number, topY: number) {
  return pathData(spindleTipUpPoints(model.spindle), centerX, topY);
}

function computeLayout(model: ToolModel) {
  const a = model.params.a;
  const marginX = Math.max(a * 1.9, unitFloor(model.params.a, 1.0));
  const topY = Math.max(a * 2.7, unitFloor(a, 1.45));
  const spacing = Math.max(a * 3.25, unitFloor(a, 1.65));
  const maxRammerLength = Math.max(...model.rammers.map((rammer) => rammer.overallLength));
  const solid = model.rammers[0];
  const spindleGapBelowSolid = Math.max(a * 0.45, unitFloor(a, 0.22));
  const spindleExtraBelowLongest = Math.max(a * 0.8, unitFloor(a, 0.45));
  const spindleTopY = Math.max(
    topY + solid.overallLength + spindleGapBelowSolid,
    topY + maxRammerLength - model.spindle.totalLength + spindleExtraBelowLongest,
  );

  const parts: LayoutPart[] = [];
  const solidX = marginX;
  parts.push({ key: "spindle", label: "Spindle", centerX: solidX, topY: spindleTopY, kind: "spindle" });
  model.rammers.forEach((rammer, index) => {
    parts.push({
      key: rammer.key,
      label: rammer.label,
      centerX: solidX + index * spacing,
      topY,
      kind: "rammer",
      rammer,
    });
  });

  const lastX = solidX + (model.rammers.length - 1) * spacing;
  const width = lastX + Math.max(a * 2.7, unitFloor(a, 1.45));
  const height = Math.max(spindleTopY + model.spindle.totalLength, topY + maxRammerLength) + Math.max(a * 1.3, unitFloor(a, 0.75));
  return { parts, topY, width, height };
}

function unitFloor(value: number, fallbackInches: number) {
  return value > 5 ? fallbackInches * 25.4 : fallbackInches;
}

function DimensionHorizontal({ x1, x2, y, label }: { x1: number; x2: number; y: number; label: string }) {
  const tick = Math.abs(x2 - x1) * 0.12 + 0.05;
  return (
    <g className="rts-dim">
      <line x1={x1} y1={y} x2={x2} y2={y} />
      <line x1={x1} y1={y - tick} x2={x1} y2={y + tick} />
      <line x1={x2} y1={y - tick} x2={x2} y2={y + tick} />
      <text x={(x1 + x2) / 2} y={y - tick * 0.45} textAnchor="middle" className="rts-dim-text">
        {label}
      </text>
    </g>
  );
}

function DimensionVertical({ x, y1, y2, label }: { x: number; y1: number; y2: number; label: string }) {
  const tick = Math.max(Math.abs(y2 - y1) * 0.025, 0.08);
  return (
    <g className="rts-dim">
      <line x1={x} y1={y1} x2={x} y2={y2} />
      <line x1={x - tick} y1={y1} x2={x + tick} y2={y1} />
      <line x1={x - tick} y1={y2} x2={x + tick} y2={y2} />
      <text x={x + tick * 1.25} y={(y1 + y2) / 2} className="rts-dim-text" transform={`rotate(-90 ${x + tick * 1.25} ${(y1 + y2) / 2})`}>
        {label}
      </text>
    </g>
  );
}

function Leader({ x1, y1, x2, y2, label }: { x1: number; y1: number; x2: number; y2: number; label: string }) {
  return (
    <g className="rts-leader">
      <line x1={x1} y1={y1} x2={x2} y2={y2} />
      <text x={x2 + 0.04} y={y2 - 0.03} className="rts-callout-text">
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
      <line
        x1={centerX - rammer.outerDiameter / 2}
        y1={topY + rammer.grooveFromTop}
        x2={centerX + rammer.outerDiameter / 2}
        y2={topY + rammer.grooveFromTop}
        className="rts-mark"
      />
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
      <text x={layout.width / 2} y={Math.max(a * 0.8, unitFloor(a, 0.55))} textAnchor="middle" className="rts-sheet-title">
        {title}
      </text>

      {layout.parts.map((part) => {
        if (part.kind === "spindle") {
          const spindle = model.spindle;
          const tipY = part.topY;
          const rootY = part.topY + spindle.spindleLength;
          const collarTopY = part.topY + spindle.totalLength - spindle.collarHeight;
          const collarBottomY = part.topY + spindle.totalLength;
          return (
            <g key={part.key}>
              <path d={spindlePathData(model, part.centerX, part.topY)} className="rts-profile" />
              <line x1={part.centerX} y1={part.topY - a * 0.35} x2={part.centerX} y2={collarBottomY + a * 0.35} className="rts-centerline" />
              {showDimensions ? (
                <>
                  <DimensionVertical x={part.centerX + a * 1.15} y1={tipY} y2={rootY} label={formatDrawingNumber(spindle.spindleLength, unit)} />
                  <DimensionVertical x={part.centerX + a * 1.55} y1={tipY} y2={collarBottomY} label={formatDrawingNumber(spindle.totalLength, unit)} />
                  <DimensionVertical x={part.centerX - a * 1.1} y1={collarTopY} y2={collarBottomY} label={formatDrawingNumber(spindle.collarHeight, unit)} />
                  {spindle.collarRise > 0 ? (
                    <DimensionVertical x={part.centerX - a * 1.45} y1={collarTopY} y2={collarTopY + spindle.collarRise} label={formatDrawingNumber(spindle.collarRise, unit)} />
                  ) : null}
                  <Leader
                    x1={part.centerX + spindle.tipDiameter / 2}
                    y1={tipY}
                    x2={part.centerX + a * 1.25}
                    y2={tipY + a * 0.25}
                    label={`tip ${formatDrawingNumber(spindle.tipDiameter, unit)}`}
                  />
                  <Leader
                    x1={part.centerX + spindle.rootDiameter / 2}
                    y1={rootY}
                    x2={part.centerX + a * 1.35}
                    y2={rootY + a * 0.16}
                    label={`root ${formatDrawingNumber(spindle.rootDiameter, unit)}`}
                  />
                  <Leader
                    x1={part.centerX + spindle.tubeDiameter / 2}
                    y1={collarBottomY}
                    x2={part.centerX + a * 1.35}
                    y2={collarBottomY - a * 0.35}
                    label={`collar ${formatDrawingNumber(spindle.tubeDiameter, unit)}`}
                  />
                  <Leader
                    x1={part.centerX + spindle.rootDiameter / 2}
                    y1={rootY}
                    x2={part.centerX + a * 1.55}
                    y2={rootY + a * 0.55}
                    label={`${formatDrawingNumber(model.params.e, unit)}° side`}
                  />
                  <Leader
                    x1={part.centerX + spindle.rootDiameter / 2}
                    y1={collarTopY + spindle.collarRise}
                    x2={part.centerX + a * 1.52}
                    y2={collarBottomY - a * 0.08}
                    label={`${formatDrawingNumber(model.params.g, unit)}° collar`}
                  />
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
        return (
          <g key={part.key}>
            <RammerShape rammer={rammer} centerX={part.centerX} topY={part.topY} />
            {showDimensions ? (
              <>
                <DimensionHorizontal
                  x1={part.centerX - rammer.outerDiameter / 2}
                  x2={part.centerX + rammer.outerDiameter / 2}
                  y={topY - dimLift}
                  label={formatDrawingNumber(rammer.outerDiameter, unit)}
                />
                <DimensionVertical x={part.centerX + rammer.outerDiameter * 1.25} y1={topY} y2={topY + rammer.headLength} label={formatDrawingNumber(rammer.headLength, unit)} />
                <DimensionVertical x={part.centerX + rammer.outerDiameter * 1.75} y1={topY} y2={bottomY} label={formatDrawingNumber(rammer.overallLength, unit)} />
                {rammer.boreDepth > 0 && rammer.boreDiameter > 0 ? (
                  <>
                    <DimensionVertical
                      x={part.centerX + rammer.outerDiameter * 2.2}
                      y1={bottomY - rammer.boreDepth}
                      y2={bottomY}
                      label={formatDrawingNumber(rammer.boreDepth, unit)}
                    />
                    <DimensionHorizontal
                      x1={part.centerX - rammer.boreDiameter / 2}
                      x2={part.centerX + rammer.boreDiameter / 2}
                      y={bottomY + dimLift * 0.72}
                      label={formatDrawingNumber(rammer.boreDiameter, unit)}
                    />
                  </>
                ) : null}
                {rammer.hasTaper ? (
                  <Leader
                    x1={part.centerX + rammer.boreDiameter / 2}
                    y1={bottomY}
                    x2={part.centerX + rammer.outerDiameter * 1.5}
                    y2={bottomY - rammer.taperHeight - rammer.outerDiameter * 0.45}
                    label={`${formatDrawingNumber(rammer.noseAngle, unit)}°`}
                  />
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

function DesignerView({
  presetKey,
  setPresetKey,
  params,
  setParams,
  unit,
  setUnit,
}: {
  presetKey: string;
  setPresetKey: (value: string) => void;
  params: ToolParams;
  setParams: (value: ToolParams) => void;
  unit: Unit;
  setUnit: (value: Unit) => void;
}) {
  const [showDimensions, setShowDimensions] = useState(true);
  const [activeHelper, setActiveHelper] = useState<{ key: keyof ToolParams; top: number; left: number } | null>(null);
  const assumption = baselineAssumption;
  const model = useMemo(() => buildToolModel(params, assumption), [params, assumption]);
  const isCustom = presetKey === "custom";

  const setField = (key: keyof ToolParams, value: number) => {
    if (!isCustom && key !== "a") {
      return;
    }
    if (!isCustom && key === "a") {
      setParams(getPreset(presetKey).derive(value));
      return;
    }
    setParams({ ...params, [key]: key === "h" ? Math.round(value) : value });
  };

  const showHelper = (key: keyof ToolParams, element: HTMLLabelElement) => {
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
          <span>Rocket type</span>
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
                  setUnit("mm");
                }
              }}
            >
              Millimeters
            </button>
          </div>
        </div>

        <div className="control-block">
          <span className="control-label">Interpretation</span>
          <p className="microcopy">{assumption.notes}</p>
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

function HarnessView({ harnessPreset, setHarnessPreset }: { harnessPreset: string; setHarnessPreset: (value: string) => void }) {
  const params = harnessPreset === "custom" ? makeDefaultParams() : getPreset(harnessPreset).derive(0.75);

  return (
    <div className="harness-shell">
      <section className="harness-controls-simple">
        <label>
          <span>Preset </span>
          <select value={harnessPreset} onChange={(event: ChangeEvent<HTMLSelectElement>) => setHarnessPreset(event.target.value)}>
            {presets.map((preset) => (
              <option key={preset.key} value={preset.key}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>
        <p>The harness renders candidate assumption sets directly. It no longer embeds old screenshots.</p>
      </section>

      <section className="candidate-grid">
        {harnessAssumptions.map((assumption) => {
          const model = buildToolModel(params, assumption);
          return (
            <article key={assumption.key} className="candidate-card">
              <div className="candidate-head">
                <strong>{assumption.label}</strong>
                <span>{assumption.notes}</span>
              </div>
              <ToolingSheet model={model} presetKey={harnessPreset} unit="in" showDimensions={false} assumption={assumption} />
            </article>
          );
        })}
      </section>
    </div>
  );
}

function App() {
  const [view, setView] = useState<ViewMode>("designer");
  const [presetKey, setPresetKey] = useState(defaultPresetKey);
  const [unit, setUnit] = useState<Unit>("in");
  const [params, setParams] = useState<ToolParams>(makeDefaultParams());
  const [harnessPreset, setHarnessPreset] = useState(defaultPresetKey);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Rocket Tool Sketcher</p>
          <h1>Shared-scale tooling sheet.</h1>
          <p className="lede">The preview references the original Flash layout: one white drawing sheet, shared scale, right-side controls, aligned rammer tops, and a spindle below the solid rammer.</p>
        </div>
        <div className="hero-actions">
          <button className={view === "designer" ? "nav-button active" : "nav-button"} onClick={() => setView("designer")}>
            Designer
          </button>
          <button className={view === "harness" ? "nav-button active" : "nav-button"} onClick={() => setView("harness")}>
            Harness
          </button>
        </div>
      </header>

      {view === "designer" ? (
        <DesignerView
          presetKey={presetKey}
          setPresetKey={setPresetKey}
          params={params}
          setParams={setParams}
          unit={unit}
          setUnit={setUnit}
        />
      ) : (
        <HarnessView harnessPreset={harnessPreset} setHarnessPreset={setHarnessPreset} />
      )}
    </div>
  );
}

export default App;
