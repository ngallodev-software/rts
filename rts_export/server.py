from __future__ import annotations

import argparse
from collections import OrderedDict
import hashlib
import io
import json
import os
import tempfile
import threading
import time
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .exporters import export_tooling_set
from .model import ManufacturingSettings, ToolParams, assumption_by_key, default_manufacturing_settings
from .presets import get_preset


# CadQuery/OpenCascade performs work in native code and is not safe to run in
# parallel inside one process.  ThreadingHTTPServer is still useful here because
# it lets health checks and OPTIONS requests complete while an export is being
# built, but actual export jobs must be serialized.  Without this guard two
# quick requests can drive the process out of memory or terminate it in native
# code, making the service appear to disappear after the first download.
_EXPORT_LOCK = threading.Lock()
_DEFAULT_CACHE_TTL_SECONDS = 15 * 60
_DEFAULT_CACHE_MAX_BYTES = 128 * 1024 * 1024
_EXPORT_CACHE: OrderedDict[str, tuple[float, str, bytes]] = OrderedDict()


def _cache_ttl_seconds() -> int:
    try:
        return max(0, int(os.environ.get("RTS_EXPORT_CACHE_TTL_SECONDS", _DEFAULT_CACHE_TTL_SECONDS)))
    except ValueError:
        return _DEFAULT_CACHE_TTL_SECONDS


def _cache_key(payload: dict) -> str:
    cache_payload = {key: value for key, value in payload.items() if key != "archiveName"}
    canonical = json.dumps(cache_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _cache_max_bytes() -> int:
    try:
        return max(0, int(os.environ.get("RTS_EXPORT_CACHE_MAX_BYTES", _DEFAULT_CACHE_MAX_BYTES)))
    except ValueError:
        return _DEFAULT_CACHE_MAX_BYTES


def _remove_expired_cache_entries(now: float) -> None:
    for key, (expires_at, _archive_name, _archive_bytes) in list(_EXPORT_CACHE.items()):
        if expires_at <= now:
            del _EXPORT_CACHE[key]


def _trim_cache_to_size(max_bytes: int) -> None:
    total_bytes = sum(len(entry[2]) for entry in _EXPORT_CACHE.values())
    while _EXPORT_CACHE and total_bytes > max_bytes:
        _key, (_expires_at, _archive_name, archive_bytes) = _EXPORT_CACHE.popitem(last=False)
        total_bytes -= len(archive_bytes)


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


def _filename_slug(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    return "-".join(part for part in slug.split("-") if part) or "custom"


def _design_file_prefix(preset_key: str, params: ToolParams, unit: str) -> str:
    diameter = f"{params.a:.6f}".rstrip("0").rstrip(".")
    return f"{_filename_slug(preset_key)}-{diameter}{'mm' if unit == 'mm' else 'in'}"


def _build_zip(payload: dict) -> tuple[str, bytes]:
    artifact_key = payload.get("artifactKey")
    if artifact_key not in {"review", "combined-dxf", "part-dxf", "pdf", "step", "stl", "openscad", "manifest"}:
        raise ValueError(f"Unknown artifact key: {artifact_key!r}")

    preset_key = str(payload.get("presetKey", "custom"))
    unit = str(payload.get("unit", "in"))
    assumption_key = str(payload.get("assumptionKey", "baseline"))
    params = _params_from_payload(payload)
    manufacturing = _manufacturing_from_payload(payload, unit)
    include_illustrative_tube = bool(payload.get("includeIllustrativeTube", False))
    assumption = assumption_by_key(assumption_key)
    preset = None if preset_key == "custom" else get_preset(preset_key)
    file_prefix = _design_file_prefix(preset_key, params, unit)

    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "export"
        bundle = export_tooling_set(
            output_dir=output_dir,
            params=params,
            assumption=assumption,
            unit=unit,
            preset=preset,
            manufacturing=manufacturing,
            include_illustrative_tube=include_illustrative_tube,
            artifact_key=artifact_key,
        )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _add_file(archive, bundle.version_manifest, f"{file_prefix}-version-manifest.json")
            if artifact_key == "review":
                _add_file(archive, bundle.manifest, f"{file_prefix}-tooling-set.json")
                _add_file(archive, bundle.openscad, f"{file_prefix}-tooling-set.scad")
                archive.writestr(
                    f"{file_prefix}-README.txt",
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
                _add_file(archive, bundle.manifest, f"{file_prefix}-tooling-manifest.json")
            elif artifact_key == "openscad":
                _add_file(archive, bundle.openscad, f"{file_prefix}-tooling-set.scad")
            elif artifact_key == "combined-dxf":
                _add_file(archive, bundle.combined_annotated_dxf, f"drawings/{file_prefix}-combined-annotated-drawing.dxf")
                _add_file(archive, bundle.combined_annotated_pdf, f"drawings/{file_prefix}-combined-annotated-drawing.pdf")
            elif artifact_key == "part-dxf":
                for path in bundle.separate_dxfs:
                    _add_file(archive, path, f"drawings/{file_prefix}-{Path(path).name}")
                for path in bundle.separate_annotated_pdfs:
                    _add_file(archive, path, f"drawings/{file_prefix}-{Path(path).name}")
            elif artifact_key == "pdf":
                _add_file(archive, bundle.combined_annotated_pdf, f"drawings/{file_prefix}-annotated-drawing.pdf")
            elif artifact_key == "step":
                _add_file(archive, bundle.combined_step, f"solids/{file_prefix}-combined-tooling.step")
                for path in bundle.separate_steps:
                    _add_file(archive, path, f"solids/{file_prefix}-{Path(path).name}")
            elif artifact_key == "stl":
                _add_file(archive, bundle.combined_stl, f"solids/{file_prefix}-combined-tooling.stl")
                for path in bundle.separate_stls:
                    _add_file(archive, path, f"solids/{file_prefix}-{Path(path).name}")

        archive_suffix = {
            "review": "review-bundle.zip",
            "manifest": "tooling-manifest.zip",
            "openscad": "openscad-model.zip",
            "combined-dxf": "combined-dxf-drawing.zip",
            "part-dxf": "per-part-dxf-drawings.zip",
            "pdf": "annotated-pdf-drawing.zip",
            "step": "step-solids.zip",
            "stl": "stl-preview-solids.zip",
        }[artifact_key]
        archive_name = f"{file_prefix}-{archive_suffix}"
        return archive_name, buffer.getvalue()


def _run_export_job(payload: dict) -> tuple[str, bytes]:
    """Return a cached archive or run one native CAD export at a time."""
    with _EXPORT_LOCK:
        ttl_seconds = _cache_ttl_seconds()
        now = time.time()
        cache_key = _cache_key(payload)
        if ttl_seconds > 0:
            _remove_expired_cache_entries(now)
            cached = _EXPORT_CACHE.get(cache_key)
            if cached is not None:
                _expires_at, archive_name, archive_bytes = cached
                return archive_name, archive_bytes

        archive_name, archive_bytes = _build_zip(payload)
        if ttl_seconds > 0:
            _EXPORT_CACHE[cache_key] = (now + ttl_seconds, archive_name, archive_bytes)
            _trim_cache_to_size(_cache_max_bytes())
        return archive_name, archive_bytes


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
            archive_name, archive_bytes = _run_export_job(payload)
        except Exception as exc:  # pragma: no cover - network boundary
            self._send_json_error(400, str(exc))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{archive_name}"')
        self.send_header("Content-Length", str(len(archive_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "Content-Disposition")
        self.end_headers()
        self.wfile.write(archive_bytes)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RTS export API server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ExportHandler)
    print(f"RTS export server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
