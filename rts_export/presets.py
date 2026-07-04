from __future__ import annotations

from dataclasses import dataclass

from .model import ToolParams


@dataclass(frozen=True)
class PresetDefinition:
    key: str
    label: str
    ratios: tuple[float, float, float, float, float, float, int, float]
    notes: str = ""

    def derive(self, tube_id: float) -> ToolParams:
        ratios = self.ratios
        return ToolParams(
            a=tube_id,
            b=tube_id * ratios[0],
            c=tube_id * ratios[1],
            d=tube_id * ratios[2],
            e=ratios[3],
            f=tube_id * ratios[4],
            g=ratios[5],
            h=int(ratios[6]),
            i=ratios[7],
        )


PRESETS: dict[str, PresetDefinition] = {
    "bp-core-burner": PresetDefinition("bp-core-burner", "BP Core burner", (10, 7.5, 0.5, 1.25, 0.75, 30, 4, 45)),
    "bp-end-burner": PresetDefinition("bp-end-burner", "BP End burner", (7, 0.75, 0.25, 1.5, 0.75, 30, 2, 30)),
    "whistle-standard": PresetDefinition("whistle-standard", "Whistle - standard", (6, 2, 0.5, 2, 0.55, 30, 3, 0)),
    "whistle-pusher": PresetDefinition("whistle-pusher", "Whistle - pusher", (6, 10 / 3, 2 / 3, 3.72, 4 / 3, 0, 3, 0)),
    "long-winded-screamer": PresetDefinition(
        "long-winded-screamer",
        "Long Winded Screamer",
        (8, 4.75 / 0.875, 0.5 / 0.875, 1.5, 0.3125 / 0.875, 20, 4, 0),
        "Uses the screenshot-validated 6in tube length at 0.75in tube I.D.",
    ),
    "stinger": PresetDefinition("stinger", "Stinger", (4, 1.5, 1 / 3, 2, 0.5, 20, 2, 35)),
    "strobe": PresetDefinition("strobe", "Strobe", (8, 4, 0.5, 1, 0.75, 30, 3, 0)),
    "fountain-gerb": PresetDefinition("fountain-gerb", "Fountain / Gerb", (7, 1, 1 / 3, 1, 0.75, 0, 2, 40)),
}

DEFAULT_PRESET_KEY = "bp-core-burner"


def get_preset(key: str) -> PresetDefinition:
    try:
        return PRESETS[key]
    except KeyError as exc:
        valid = ", ".join(sorted(PRESETS))
        raise KeyError(f"Unknown preset '{key}'. Valid keys: {valid}") from exc


def list_presets() -> list[PresetDefinition]:
    return list(PRESETS.values())
