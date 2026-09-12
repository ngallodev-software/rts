import io
import fitz
import threading
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from rts_export.exporters import export_tooling_set
from rts_export.model import BASELINE_ASSUMPTION
from rts_export.presets import get_preset
from rts_export.server import _EXPORT_CACHE, _build_zip, _run_export_job


class ExportServerLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        _EXPORT_CACHE.clear()

    def tearDown(self) -> None:
        _EXPORT_CACHE.clear()

    def test_back_to_back_exports_both_complete(self) -> None:
        with patch("rts_export.server._build_zip", side_effect=[("manifest-json.zip", b"one"), ("annotated-pdf.zip", b"two")]):
            self.assertEqual(_run_export_job({"artifactKey": "manifest"}), ("manifest-json.zip", b"one"))
            self.assertEqual(_run_export_job({"artifactKey": "pdf"}), ("annotated-pdf.zip", b"two"))

    def test_identical_export_is_served_from_cache(self) -> None:
        payload = {"artifactKey": "pdf", "params": {"a": 0.75}}
        with patch("rts_export.server._build_zip", return_value=("annotated-pdf.zip", b"cached-pdf")) as build:
            first = _run_export_job(payload)
            second = _run_export_job({**payload, "archiveName": "ignored-client-name.zip"})

        self.assertEqual(first, ("annotated-pdf.zip", b"cached-pdf"))
        self.assertEqual(second, first)
        build.assert_called_once_with(payload)

    def test_cache_evicts_oldest_archives_first(self) -> None:
        payloads = [
            {"artifactKey": "manifest", "params": {"a": value}}
            for value in (0.75, 1.0, 1.25)
        ]
        with patch("rts_export.server._cache_max_bytes", return_value=4), patch(
            "rts_export.server._build_zip",
            side_effect=[
                ("manifest-json.zip", b"aa"),
                ("manifest-json.zip", b"bb"),
                ("manifest-json.zip", b"cc"),
                ("manifest-json.zip", b"AA"),
            ],
        ) as build:
            _run_export_job(payloads[0])
            _run_export_job(payloads[1])
            _run_export_job(payloads[0])  # A hit must not make it newer.
            _run_export_job(payloads[2])  # C pushes oldest entry A out.
            _run_export_job(payloads[0])

        self.assertEqual(build.call_count, 4)

    def test_overlapping_exports_are_serialized(self) -> None:
        active_jobs = 0
        maximum_active_jobs = 0
        state_lock = threading.Lock()
        start_together = threading.Barrier(3)
        results: list[tuple[str, bytes]] = []

        def fake_build(_payload: dict) -> tuple[str, bytes]:
            nonlocal active_jobs, maximum_active_jobs
            with state_lock:
                active_jobs += 1
                maximum_active_jobs = max(maximum_active_jobs, active_jobs)
            time.sleep(0.05)
            with state_lock:
                active_jobs -= 1
            return "annotated-pdf.zip", b"data"

        def run() -> None:
            start_together.wait()
            results.append(_run_export_job({"artifactKey": "pdf"}))

        with patch("rts_export.server._build_zip", side_effect=fake_build):
            threads = [threading.Thread(target=run) for _ in range(2)]
            for thread in threads:
                thread.start()
            start_together.wait()
            for thread in threads:
                thread.join(timeout=2)

        self.assertEqual(maximum_active_jobs, 1)
        self.assertEqual(results, [("annotated-pdf.zip", b"data"), ("annotated-pdf.zip", b"data")])

    def test_pdf_request_only_generates_pdf_and_version_manifest(self) -> None:
        preset = get_preset("bp-core-burner")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            bundle = export_tooling_set(
                output_dir=output_dir,
                params=preset.derive(0.75),
                assumption=BASELINE_ASSUMPTION,
                preset=preset,
                artifact_key="pdf",
            )

            generated_files = sorted(path.relative_to(output_dir).as_posix() for path in output_dir.rglob("*") if path.is_file())
            with fitz.open(bundle.combined_annotated_pdf) as document:
                page_text = [page.get_text() for page in document]

        self.assertEqual(generated_files, ["drawings/tooling-set-annotated.pdf", "version-manifest.json"])
        self.assertTrue(bundle.combined_annotated_pdf)
        self.assertFalse(bundle.combined_annotated_dxf)
        self.assertFalse(bundle.combined_step)
        self.assertFalse(bundle.combined_stl)
        self.assertFalse(bundle.manifest)
        self.assertFalse(bundle.openscad)
        self.assertEqual(len(page_text), preset.derive(0.75).h + 2)
        self.assertIn("tooling set - overview", page_text[0])
        self.assertIn("Spindle", page_text[1])
        self.assertIn("Full-depth 'A' rammer", page_text[2])
        self.assertIn("Solid rammer", page_text[-1])

    def test_download_names_identify_design_size_and_artifact(self) -> None:
        preset = get_preset("bp-core-burner")
        archive_name, archive_bytes = _build_zip(
            {
                "artifactKey": "manifest",
                "presetKey": preset.key,
                "unit": "in",
                "assumptionKey": "baseline",
                "params": preset.derive(0.75).as_dict(),
            }
        )

        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            contained_names = archive.namelist()

        self.assertEqual(archive_name, "bp-core-burner-0.75in-tooling-manifest.zip")
        self.assertEqual(
            contained_names,
            [
                "bp-core-burner-0.75in-version-manifest.json",
                "bp-core-burner-0.75in-tooling-manifest.json",
            ],
        )


if __name__ == "__main__":
    unittest.main()
