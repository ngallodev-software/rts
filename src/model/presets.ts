import type { PresetDefinition, ToolParams } from "./types";

function makePreset(
  key: string,
  label: string,
  ratios: [number, number, number, number, number, number, number, number],
  notes?: string,
): PresetDefinition {
  return {
    key,
    label,
    notes,
    derive: (a: number): ToolParams => ({
      a,
      b: a * ratios[0],
      c: a * ratios[1],
      d: a * ratios[2],
      e: ratios[3],
      f: a * ratios[4],
      g: ratios[5],
      h: ratios[6],
      i: ratios[7],
    }),
  };
}

export const presets: PresetDefinition[] = [
  makePreset("bp-core-burner", "BP Core burner", [10, 7.5, 0.5, 1.25, 0.75, 30, 4, 45]),
  makePreset("bp-end-burner", "BP End burner", [7, 0.75, 0.25, 1.5, 0.75, 30, 2, 30]),
  makePreset("whistle-standard", "Whistle - standard", [6, 2, 0.5, 2, 0.55, 30, 3, 0]),
  makePreset("whistle-pusher", "Whistle - pusher", [6, 10 / 3, 2 / 3, 3.72, 4 / 3, 0, 3, 0]),
  makePreset(
    "long-winded-screamer",
    "Long Winded Screamer",
    [8, 4.75 / 0.875, 0.5 / 0.875, 1.5, 0.3125 / 0.875, 20, 4, 0],
    "Uses the screenshot-validated 6in tube length at 0.75in tube I.D.",
  ),
  makePreset("stinger", "Stinger", [4, 1.5, 1 / 3, 2, 0.5, 20, 2, 35]),
  makePreset("strobe", "Strobe", [8, 4, 0.5, 1, 0.75, 30, 3, 0]),
  makePreset("fountain-gerb", "Fountain / Gerb", [7, 1, 1 / 3, 1, 0.75, 0, 2, 40]),
];

export const defaultPresetKey = "bp-core-burner";

export function getPreset(key: string) {
  return presets.find((preset) => preset.key === key) ?? presets[0];
}
