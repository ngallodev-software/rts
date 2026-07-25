from __future__ import annotations

import argparse
import io
import json
import tempfile
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .exporters import export_tooling_set
from .model import ManufacturingSettings, ToolParams, assumption_by_key, default_manufacturing_settings
from .presets import get_preset


def _params_from_payload(payload: dict) -> ToolParams:
    raw = payload.get("params")
    if not isinstance(raw, dict):
        raise ValueError("Missing params payload.")
    return ToolParams(
        a=float(raw["a"]),
        b=float(raw["b"]),
        c=float(raw["c"]),
        d=float(raw["d"]),
        e=float(raw["e"]),
        f=float(raw["f"]),
        g=float(raw["g"]),
        h=int(round(float(raw["h"]))),
        i=float(raw["i"]),
    )


def _manufacturing_from_payload(payload: dict, unit: str) -> ManufacturingSettings:
    raw = payload.get("manufacturing")
    if not isinstance(raw, dict):
        return default_manufacturing_settings("mm" if unit == "mm" else "in")
    return ManufacturingSettings(
        general_tolerance=float(raw["generalTolerance"]),
        spindle_minus_tolerance=float(raw["spindleMinusTolerance"]),
        bore_plus_tolerance=float(raw["borePlusTolerance"]),
        minimum_diametral_clearance=float(raw["minimumDiametralClearance"]),
        switch_mark_offset_diameters=float(raw["switchMarkOffsetDiameters"]),
        spindle_finish_ra=float(raw["spindleFinishRa"]),
        rammer_od_finish_ra=float(raw["rammerOdFinishRa"]),
        rammer_bore_finish_ra=float(raw["rammerBoreFinishRa"]),
    )


def _add_file(zip_file: zipfile.ZipFile, source: str | Path, arcname: str | None = None) -> None:
    path = Path(source)
    zip_file.write(path, arcname or path.as_posix().split("/")[-1])


def _build_zip(payload: dict) -> tuple[str, bytes]:
    artifact_key = payload.get("artifactKey")
    if artifact_key not in {"review", "combined-dxf", "part-dxf", "step", "stl", "openscad", "manifest"}:
        raise ValueError(f"Unknown artifact key: {artifact_key!r}")

    preset_key = str(payload.get("presetKey", "custom"))
    unit = str(payload.get("unit", "in"))
    assumption_key = str(payload.get("assumptionKey", "baseline"))
    params = _params_from_payload(payload)
    manufacturing = _manufacturing_from_payload(payload, unit)
    assumption = assumption_by_key(assumption_key)
    preset = None if preset_key == "custom" else get_preset(preset_key)

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "export"
        bundle = export_tooling_set(
            output_dir=output_dir,
            params=params,
            assumption=assumption,
            unit=unit,
            preset=preset,
            manufacturing=manufacturing,
        )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _add_file(archive, bundle.version_manifest, "version-manifest.json")
            if artifact_key == "review":
                _add_file(archive, bundle.manifest, "tooling-set.json")
                _add_file(archive, bundle.openscad, "tooling-set.scad")
                archive.writestr(
                    "README.txt",
                    "\n".join(
                        [
                            "Rocket Tooling Designer review bundle",
                            "",
                            "Includes manifest JSON and OpenSCAD for quick inspection.",
                            "Use the CAD export buttons for DXF, STEP, and STL output.",
                        ]
                    ),
                )
            elif artifact_key == "manifest":
                _add_file(archive, bundle.manifest, "tooling-set.json")
            elif artifact_key == "openscad":
                _add_file(archive, bundle.openscad, "tooling-set.scad")
            elif artifact_key == "combined-dxf":
                _add_file(archive, bundle.combined_annotated_dxf, "drawings/tooling-set-annotated.dxf")
                _add_file(archive, bundle.combined_annotated_pdf, "drawings/tooling-set-annotated.pdf")
            elif artifact_key == "part-dxf":
                for path in bundle.separate_dxfs:
                    _add_file(archive, path, Path(path).relative_to(output_dir).as_posix())
                for path in bundle.separate_annotated_pdfs:
                    _add_file(archive, path, Path(path).relative_to(output_dir).as_posix())
            elif artifact_key == "step":
                _add_file(archive, bundle.combined_step, "solids/tooling-set.step")
                for path in bundle.separate_steps:
                    _add_file(archive, path, Path(path).relative_to(output_dir).as_posix())
            elif artifact_key == "stl":
                _add_file(archive, bundle.combined_stl, "solids/tooling-set.stl")
                for path in bundle.separate_stls:
                    _add_file(archive, path, Path(path).relative_to(output_dir).as_posix())

        archive_name = {
            "review": "review-bundle.zip",
            "manifest": "manifest-json.zip",
            "openscad": "openscad.zip",
            "combined-dxf": "combined-dxf.zip",
            "part-dxf": "per-part-dxf.zip",
            "step": "step-solids.zip",
            "stl": "stl-preview-solids.zip",
        }[artifact_key]
        return archive_name, buffer.getvalue()


class ExportHandler(BaseHTTPRequestHandler):
    server_version = "RTSExportServer/1.0.0"

    def _send_json_error(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/healthz":
            self._send_json_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/export":
            self._send_json_error(404, "Not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            archive_name, archive_bytes = _build_zip(payload)
        except Exception as exc:  # pragma: no cover - network boundary
            self._send_json_error(400, str(exc))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{archive_name}"')
        self.send_header("Content-Length", str(len(archive_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(archive_bytes)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RTS export API server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ExportHandler)
    print(f"RTS export server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
