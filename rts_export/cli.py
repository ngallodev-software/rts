from __future__ import annotations

import argparse
import json
from pathlib import Path

from .exporters import export_tooling_set
from .model import BASELINE_ASSUMPTION, ToolParams, assumption_by_key
from .presets import DEFAULT_PRESET_KEY, get_preset, list_presets


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate CAD exports for Rocket Tool Sketcher tooling.")
    parser.add_argument("--preset", default=DEFAULT_PRESET_KEY, help="Preset key to derive from, or 'custom'.")
    parser.add_argument("--tube-id", type=float, default=0.75, help="Tube I.D. used to derive preset dimensions.")
    parser.add_argument("--unit", choices=["in", "mm"], default="in", help="Length unit for the generated output files.")
    parser.add_argument("--assumption", default=BASELINE_ASSUMPTION.key, help="Assumption set key.")
    parser.add_argument("--output", type=Path, default=Path("exports") / "sample", help="Output directory.")
    parser.add_argument("--list-presets", action="store_true", help="List available preset keys and exit.")
    parser.add_argument("--a", type=float)
    parser.add_argument("--b", type=float)
    parser.add_argument("--c", type=float)
    parser.add_argument("--d", type=float)
    parser.add_argument("--e", type=float)
    parser.add_argument("--f", type=float)
    parser.add_argument("--g", type=float)
    parser.add_argument("--h", type=int)
    parser.add_argument("--i", type=float)
    return parser


def _custom_params_from_args(args: argparse.Namespace) -> ToolParams:
    missing = [key for key in "abcdefghi" if getattr(args, key) is None]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Custom mode requires explicit A-I values. Missing: {joined}")
    return ToolParams(
        a=args.a,
        b=args.b,
        c=args.c,
        d=args.d,
        e=args.e,
        f=args.f,
        g=args.g,
        h=args.h,
        i=args.i,
    )


def main() -> None:
    parser = _parser()
    args = parser.parse_args()

    if args.list_presets:
        for preset in list_presets():
            print(f"{preset.key}: {preset.label}")
        return

    assumption = assumption_by_key(args.assumption)

    if args.preset == "custom":
        params = _custom_params_from_args(args)
        preset = None
    else:
        preset = get_preset(args.preset)
        params = preset.derive(args.tube_id)

    bundle = export_tooling_set(
        output_dir=args.output,
        params=params,
        assumption=assumption,
        unit=args.unit,
        preset=preset,
    )
    print(json.dumps(bundle.__dict__, indent=2))


if __name__ == "__main__":
    main()
