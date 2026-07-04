import { useMemo, useState } from "react";
import { baselineAssumption, harnessAssumptions } from "./model/assumptions";
import { fieldMeta } from "./model/fields";
import { buildToolModel, convertParams, formatDimension } from "./model/geometry";
import { defaultPresetKey, getPreset, presets } from "./model/presets";
import type { AssumptionSet, RammerModel, ToolParams, Unit } from "./model/types";

type ViewMode = "designer" | "harness";

const referenceByPreset: Record<string, string> = {
  "bp-core-burner": "/references/01-bp-core-burner-0.75in.png",
  "bp-end-burner": "/references/02-bp-end-burner-0.75in.png",
  "whistle-standard": "/references/03-whistle-standard-0.75in.png",
  "whistle-pusher": "/references/04-whistle-pusher-0.75in.png",
  "long-winded-screamer": "/references/05-long-winded-screamer-0.75in.png",
  stinger: "/references/06-stinger-0.75in.png",
  strobe: "/references/07-strobe-0.75in.png",
  "fountain-gerb": "/references/08-fountain-gerb-0.75in.png",
  custom: "/references/09-custom-whistle-example.png",
};

function makeDefaultParams() {
  return getPreset(defaultPresetKey).derive(0.75);
}

function pointsToSvg(points: [number, number][]) {
  return points.map(([x, y]) => `${x},${y}`).join(" ");
}

function scalePart(points: [number, number][], width: number, height: number, padding = 18) {
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanX = Math.max(maxX - minX, 0.001);
  const spanY = Math.max(maxY - minY, 0.001);
  const scale = Math.min((width - padding * 2) / spanX, (height - padding * 2) / spanY);

  return points.map(([x, y]) => [
    padding + (x - minX) * scale,
    padding + (y - minY) * scale,
  ] as [number, number]);
}

function BoreLines({ rammer }: { rammer: RammerModel }) {
  if (rammer.boreDepth <= 0 || rammer.boreDiameter <= 0) {
    return null;
  }

  const half = rammer.boreDiameter / 2;
  const scaled = scalePart(
    [
      [-half, rammer.overallLength - rammer.boreDepth],
      [-half, rammer.overallLength],
      [half, rammer.overallLength],
      [half, rammer.overallLength - rammer.boreDepth],
    ],
    120,
    260,
  );

  return (
    <g className="bore-lines">
      <line x1={scaled[0][0]} y1={scaled[0][1]} x2={scaled[1][0]} y2={scaled[1][1]} />
      <line x1={scaled[3][0]} y1={scaled[3][1]} x2={scaled[2][0]} y2={scaled[2][1]} />
      <line x1={scaled[0][0]} y1={scaled[0][1]} x2={scaled[3][0]} y2={scaled[3][1]} />
    </g>
  );
}

function RammerCard({ rammer, unit }: { rammer: RammerModel; unit: Unit }) {
  const scaled = scalePart(rammer.points, 120, 260);
  return (
    <div className="rammer-card">
      <svg viewBox="0 0 120 260" className="rammer-svg">
        <polygon points={pointsToSvg(scaled)} className="profile-shape" />
        <BoreLines rammer={rammer} />
      </svg>
      <div className="rammer-copy">
        <strong>{rammer.label}</strong>
        <span>Length {formatDimension(rammer.overallLength, unit)}</span>
        {rammer.boreDepth > 0 ? (
          <span>
            Bore {formatDimension(rammer.boreDiameter, unit)} x {formatDimension(rammer.boreDepth, unit)}
          </span>
        ) : (
          <span>No bore</span>
        )}
        {rammer.hasTaper ? <span>Nose {rammer.noseAngle.toFixed(2)}°</span> : null}
      </div>
    </div>
  );
}

function SpindleCard({
  points,
  unit,
  totalLength,
  tipDiameter,
}: {
  points: [number, number][];
  unit: Unit;
  totalLength: number;
  tipDiameter: number;
}) {
  const scaled = scalePart(points, 180, 320);
  return (
    <div className="spindle-card">
      <svg viewBox="0 0 180 320" className="spindle-svg">
        <polygon points={pointsToSvg(scaled)} className="profile-shape" />
      </svg>
      <div className="rammer-copy">
        <strong>Spindle</strong>
        <span>Length {formatDimension(totalLength, unit)}</span>
        <span>Tip {formatDimension(tipDiameter, unit)}</span>
      </div>
    </div>
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
  const assumption = baselineAssumption;
  const model = useMemo(() => buildToolModel(params, assumption), [params]);
  const isCustom = presetKey === "custom";

  const setField = (key: keyof ToolParams, value: number) => {
    if (!isCustom && key !== "a") {
      return;
    }
    const next = { ...params, [key]: key === "h" ? Math.round(value) : value };
    if (!isCustom && key === "a") {
      setParams(getPreset(presetKey).derive(value));
      return;
    }
    setParams(next);
  };

  return (
    <div className="layout">
      <aside className="panel controls">
        <div className="section">
          <label className="field">
            <span>Rocket type</span>
            <select
              value={presetKey}
              onChange={(event) => {
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
        </div>

        <div className="section two-up">
          <label className="field">
            <span>Units</span>
            <div className="toggle-row">
              <button
                className={unit === "in" ? "chip chip-active" : "chip"}
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
                className={unit === "mm" ? "chip chip-active" : "chip"}
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
          </label>
          <div className="field">
            <span>Interpretation</span>
            <p className="microcopy">{assumption.notes}</p>
          </div>
        </div>

        <div className="section grid-fields">
          {fieldMeta.map((field) => (
            <label key={field.key} className="field">
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
                onChange={(event) => setField(field.key, Number(event.target.value))}
              />
            </label>
          ))}
        </div>
      </aside>

      <main className="canvas-stack">
        <section className="panel blueprint">
          <div className="sheet-header">
            <div>
              <p className="sheet-kicker">{presetKey === "custom" ? "Custom tooling" : getPreset(presetKey).label}</p>
              <h2>{formatDimension(params.a, unit)} tooling set</h2>
            </div>
            <div className="sheet-meta">
              <span>{params.h} rammers</span>
              <span>Finished dimensions</span>
            </div>
          </div>

          <div className="part-row">
            <SpindleCard
              points={model.spindle.points}
              unit={unit}
              totalLength={model.spindle.totalLength}
              tipDiameter={model.spindle.tipDiameter}
            />
            {model.rammers.map((rammer) => (
              <RammerCard key={rammer.key} rammer={rammer} unit={unit} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

function HarnessCandidate({
  params,
  assumption,
  unit,
}: {
  params: ToolParams;
  assumption: AssumptionSet;
  unit: Unit;
}) {
  const model = useMemo(() => buildToolModel(params, assumption), [params, assumption]);
  return (
    <article className="candidate-card">
      <div className="candidate-head">
        <strong>{assumption.label}</strong>
        <span>{assumption.notes}</span>
      </div>
      <div className="candidate-parts">
        <SpindleCard
          points={model.spindle.points}
          unit={unit}
          totalLength={model.spindle.totalLength}
          tipDiameter={model.spindle.tipDiameter}
        />
        <RammerCard rammer={model.rammers[1]} unit={unit} />
      </div>
    </article>
  );
}

function HarnessView({
  harnessPreset,
  setHarnessPreset,
}: {
  harnessPreset: string;
  setHarnessPreset: (value: string) => void;
}) {
  const params = harnessPreset === "custom" ? makeDefaultParams() : getPreset(harnessPreset).derive(0.75);
  const referencePath = referenceByPreset[harnessPreset];

  return (
    <div className="harness-shell">
      <section className="panel harness-controls">
        <label className="field">
          <span>Reference preset</span>
          <select value={harnessPreset} onChange={(event) => setHarnessPreset(event.target.value)}>
            {presets.map((preset) => (
              <option key={preset.key} value={preset.key}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>
        <p className="microcopy">
          This harness is intentionally narrow. It compares candidate `E/G/I` assumptions and groove rendering against
          the original screenshot for a single preset at a time.
        </p>
      </section>

      <div className="harness-layout">
        <section className="panel reference-panel">
          <div className="sheet-header">
            <div>
              <p className="sheet-kicker">Reference</p>
              <h2>{getPreset(harnessPreset).label}</h2>
            </div>
          </div>
          <img src={referencePath} alt={`${harnessPreset} reference`} className="reference-image" />
        </section>

        <section className="candidate-grid">
          {harnessAssumptions.map((assumption) => (
            <HarnessCandidate key={assumption.key} params={params} assumption={assumption} unit="in" />
          ))}
        </section>
      </div>
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
      <div className="hero">
        <div>
          <p className="eyebrow">Rocket Tool Sketcher</p>
          <h1>Refactored geometry model with a first-pass comparison harness.</h1>
          <p className="lede">
            The app now uses shared spindle and rammer geometry, modular presets, and a side-by-side harness for
            locking the remaining `E/G/I` conventions before CAD export work resumes.
          </p>
        </div>
        <div className="hero-actions">
          <button className={view === "designer" ? "action" : "action action-secondary"} onClick={() => setView("designer")}>
            Designer
          </button>
          <button className={view === "harness" ? "action" : "action action-secondary"} onClick={() => setView("harness")}>
            Harness
          </button>
        </div>
      </div>

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
