from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_MANIFEST_PATH = PROJECT_ROOT / "version-manifest.json"


def load_version_manifest() -> dict:
    return json.loads(VERSION_MANIFEST_PATH.read_text(encoding="utf-8"))


def write_version_manifest(path: Path) -> str:
    payload = load_version_manifest()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return str(path)
