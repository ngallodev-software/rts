import unittest

from rts_export.model import (
    BASELINE_ASSUMPTION,
    ManufacturingSettings,
    build_tool_model,
    default_manufacturing_settings,
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
