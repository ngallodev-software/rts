from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import ezdxf
import fitz
from ezdxf import bbox


EXPECTED_COMPONENTS = {
    "web",
    "export_api",
    "geometry_model",
    "dxf_clean",
    "dxf_annotated",
    "pdf_annotated",
    "step",
    "stl",
    "openscad",
    "tooling_manifest",
    "verification_harness",
}
EXPECTED_ZONES = ["spindle", "solid", "a-rammer", "progressive-1", "progressive-2", "overview"]


@dataclass
class VerificationReport:
    export_dir: str
    checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def check(self, condition: bool, message: str) -> None:
        if condition:
            self.checks.append(message)
        else:
            self.failures.append(message)


def require_file(report: VerificationReport, path: Path, minimum_size: int = 1) -> None:
    report.check(path.is_file(), f"exists: {path.name}")
    if path.is_file():
        report.check(path.stat().st_size >= minimum_size, f"nonempty: {path.name}")


def verify_versions(report: VerificationReport, export_dir: Path, project_root: Path) -> None:
    root_path = project_root / "version-manifest.json"
    exported_path = export_dir / "version-manifest.json"
    tooling_path = export_dir / "tooling-set.json"
    for path in (root_path, exported_path, tooling_path):
        require_file(report, path)
    if not all(path.is_file() for path in (root_path, exported_path, tooling_path)):
        return
    root = json.loads(root_path.read_text(encoding="utf-8"))
    exported = json.loads(exported_path.read_text(encoding="utf-8"))
    tooling = json.loads(tooling_path.read_text(encoding="utf-8"))
    report.check(root == exported, "exported version manifest matches project manifest")
    report.check(tooling.get("versions") == root, "tooling manifest embeds project component versions")
    report.check(set(root.get("components", {})) == EXPECTED_COMPONENTS, "all functional components are versioned")


def verify_dxf(report: VerificationReport, export_dir: Path) -> None:
    drawings = export_dir / "drawings"
    dxfs = sorted(drawings.glob("*.dxf"))
    report.check(len(dxfs) == 18, "expected 18 combined/separate DXF files")
    for path in dxfs:
        document = ezdxf.readfile(path)
        auditor = document.audit()
        report.check(not auditor.errors and not auditor.fixes, f"DXF audit clean: {path.name}")

    combined = drawings / "tooling-set-annotated.dxf"
    require_file(report, combined, 1000)
    if not combined.is_file():
        return
    document = ezdxf.readfile(combined)
    msp = document.modelspace()
    report.check(document.header.get("$INSUNITS") in {1, 4}, "annotated DXF declares inch or millimeter units")
    required_layers = {"PROFILE", "HIDDEN", "CENTER", "DIM", "TEXT", "TITLE", "MARKS", "NOTES", "TABLE"}
    report.check(required_layers.issubset({layer.dxf.name for layer in document.layers}), "annotated DXF has all required layers")

    texts = [entity.dxf.text for entity in msp.query("TEXT")]
    report.check(any(chr(176) in text for text in texts), "degree symbols are present")
    report.check(not any(" DEG" in text for text in texts), "legacy DEG angle labels are absent")
    mark_count = sum(entity.dxf.layer == "MARKS" for entity in msp.query("LINE"))
    report.check(mark_count == 7, "canonical set has four do-not-pass and three switch-rammer marks")

    zones: dict[str, list] = {}
    for entity in msp:
        if not entity.has_xdata("RTS_QA"):
            continue
        tags = entity.get_xdata("RTS_QA")
        zone = str(tags[0].value)
        zones.setdefault(zone, []).append(entity)
    report.check(list(zones) == EXPECTED_ZONES, "annotated DXF contains the expected ordered QA zones")
    if list(zones) != EXPECTED_ZONES:
        return
    zone_extents = [(name, bbox.extents(entities, fast=True)) for name, entities in zones.items()]
    for (left_name, left), (right_name, right) in zip(zone_extents, zone_extents[1:]):
        gap = right.extmin.x - left.extmax.x
        report.check(gap >= 0.49, f"zones separated: {left_name} -> {right_name} ({gap:.3f} drawing units)")


def verify_pdf(report: VerificationReport, export_dir: Path) -> None:
    path = export_dir / "drawings" / "tooling-set-annotated.pdf"
    require_file(report, path, 1000)
    if not path.is_file():
        return
    document = fitz.open(path)
    report.check(document.page_count == 4, "canonical combined PDF has four pages")
    for index, page in enumerate(document, start=1):
        report.check(page.rect.width > page.rect.height, f"PDF page {index} is landscape")
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        render_path = export_dir / f"verification-pdf-page-{index}.png"
        pixmap.save(render_path)
        report.check(render_path.stat().st_size > 1000, f"PDF page {index} rendered for visual review")
    page_four_text = document[3].get_text()
    report.check("MINIMUM SPINDLE-TO-BORE" in page_four_text, "PDF notes page contains fit requirements")
    report.check("PROG RAMMER 2" in page_four_text, "PDF summary table contains the final rammer")


def verify_solids_and_openscad(report: VerificationReport, export_dir: Path) -> None:
    solids = export_dir / "solids"
    step_files = sorted(solids.glob("*.step"))
    stl_files = sorted(solids.glob("*.stl"))
    report.check(len(step_files) == 6, "combined plus five separate STEP files exist")
    report.check(len(stl_files) == 6, "combined plus five separate STL files exist")
    for path in step_files + stl_files:
        require_file(report, path, 1000)
    openscad = export_dir / "tooling-set.scad"
    require_file(report, openscad, 500)
    if openscad.is_file():
        content = openscad.read_text(encoding="utf-8")
        report.check("module spindle" in content, "OpenSCAD contains spindle module")
        rammer_modules = ["module solid", "module a_rammer", "module progressive_1", "module progressive_2"]
        report.check(all(name in content for name in rammer_modules), "OpenSCAD contains all four rammer modules")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an RTS export bundle against the release checklist.")
    parser.add_argument("export_dir", type=Path)
    args = parser.parse_args()
    export_dir = args.export_dir.resolve()
    project_root = Path(__file__).resolve().parent.parent
    report = VerificationReport(str(export_dir))

    report.check(export_dir.is_dir(), "export directory exists")
    if export_dir.is_dir():
        verify_versions(report, export_dir, project_root)
        verify_dxf(report, export_dir)
        verify_pdf(report, export_dir)
        verify_solids_and_openscad(report, export_dir)

    report_path = export_dir / "verification-report.json"
    report_path.write_text(json.dumps(report.__dict__, indent=2) + "\n", encoding="utf-8")
    for message in report.checks:
        print(f"PASS: {message}")
    for message in report.failures:
        print(f"FAIL: {message}", file=sys.stderr)
    print(f"Report: {report_path}")
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
