import unittest

from rts_export.versioning import load_version_manifest


class VersionManifestTests(unittest.TestCase):
    def test_all_functional_components_are_versioned(self) -> None:
        manifest = load_version_manifest()
        expected = {
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
        self.assertEqual(set(manifest["components"]), expected)

    def test_annotated_dxf_layout_release_is_versioned(self) -> None:
        manifest = load_version_manifest()
        self.assertEqual(manifest["release"], "1.1.0")
        self.assertEqual(manifest["components"]["dxf_annotated"]["version"], "1.1.0")


if __name__ == "__main__":
    unittest.main()
