import unittest

from rts_export.model import (
    BASELINE_ASSUMPTION,
    ManufacturingSettings,
    SpindleBaseSettings,
    build_tool_model,
    default_manufacturing_settings,
    default_spindle_base_settings,
    validate_manufacturing_settings,
)
from rts_export.presets import get_preset


class ManufacturingModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = get_preset("bp-core-burner").derive(0.75)

    def test_legacy_and_switch_marks(self) -> None:
        model = build_tool_model(self.params, BASELINE_ASSUMPTION, default_manufacturing_settings("in"))
        self.assertAlmostEqual(model.rammers[0].groove_from_top, 1.125)
        self.assertAlmostEqual(model.rammers[0].switch_mark_from_top or 0, 1.875)
        self.assertIsNone(model.rammers[-1].switch_mark_from_top)

    def test_spindle_base_enforces_confirmed_minimums(self) -> None:
        settings = SpindleBaseSettings(True, "square", 0.5, 0.5, 0.25, 0.05, "1/4-20", 0.266, 0.438, 0.25, 0.375)
        model = build_tool_model(self.params, BASELINE_ASSUMPTION, default_manufacturing_settings(), settings)
        self.assertGreaterEqual(model.spindle_base.size, model.params.a + 0.25)
        self.assertGreaterEqual(model.spindle_base.height, 1.5)
        self.assertGreaterEqual(model.spindle_base.extension_diameter, model.params.a)
        self.assertGreaterEqual(model.spindle_base.size, model.spindle_base.extension_diameter + 0.25)

    def test_default_spindle_base_matches_starting_stock(self) -> None:
        base = default_spindle_base_settings()
        self.assertFalse(base.enabled)
        self.assertEqual((base.shape, base.size, base.height), ("square", 1.25, 1.5))
        self.assertEqual((base.extension_diameter, base.fastener_thread), (1.0, "1/4-20"))

    def test_clearance_must_be_positive(self) -> None:
        settings = ManufacturingSettings(0.002, 0.001, 0.001, 0.0, 1.0, 32, 32, 63)
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            validate_manufacturing_settings(settings, self.params.a)

    def test_clearance_has_scale_aware_upper_bound(self) -> None:
        settings = ManufacturingSettings(0.002, 0.001, 0.001, 0.08, 1.0, 32, 32, 63)
        with self.assertRaisesRegex(ValueError, "10%"):
            validate_manufacturing_settings(settings, self.params.a)


if __name__ == "__main__":
    unittest.main()
