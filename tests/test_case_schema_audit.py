import unittest

from scripts import audit_case_schema as audit


class CaseSchemaAuditTest(unittest.TestCase):
    def test_valid_minimal_case_passes(self) -> None:
        case = {
            "schema_version": audit.SUPPORTED_SCHEMA_VERSION,
            "case_id": "schema_smoke",
            "terrain": {"type": "plane", "parameters": {"z0_m": 0.0}},
            "parameters": {"contact_model": "translational_v0"},
        }

        self.assertEqual(audit.audit_case_data(case, "case.yaml"), [])

    def test_missing_schema_version_and_unknown_keys_fail(self) -> None:
        case = {
            "case_id": "bad",
            "terrain": {"type": "plane", "typo": True},
            "unexpected": True,
        }

        errors = audit.audit_case_data(case, "bad.yaml")

        self.assertIn("bad.yaml: missing schema_version", errors)
        self.assertIn("bad.yaml: unknown top-level key 'unexpected'", errors)
        self.assertIn("bad.yaml: unknown terrain.typo", errors)

    def test_unknown_deep_structural_keys_fail(self) -> None:
        case = {
            "schema_version": audit.SUPPORTED_SCHEMA_VERSION,
            "case_id": "bad_nested",
            "terrain": {"type": "plane", "parameters": {"z0_m": 0.0, "slope_typo": 0.1}},
            "hazard_probability": {
                "probability_model": "sampling_weighted",
                "metadata_path": "metadata.csv",
                "weight_column": "sampling_weight",
                "normalization_convention": "conditioned_on_filter",
                "filters": {"source_zone_ids": [], "source_zone_typo": []},
            },
        }

        errors = audit.audit_case_data(case, "bad_nested.yaml")

        self.assertIn("bad_nested.yaml: unknown terrain.parameters.slope_typo", errors)
        self.assertIn(
            "bad_nested.yaml: unknown hazard_probability.filters.source_zone_typo",
            errors,
        )

    def test_expected_metric_names_remain_extensible(self) -> None:
        case = {
            "schema_version": audit.SUPPORTED_SCHEMA_VERSION,
            "case_id": "custom_metrics",
            "terrain": {"type": "plane", "parameters": {"z0_m": 0.0}},
            "expected": {
                "tolerances": {"new_metric_error": 0.1},
                "values": {"new_count_metric": 2.0},
            },
        }

        self.assertEqual(audit.audit_case_data(case, "custom_metrics.yaml"), [])


if __name__ == "__main__":
    unittest.main()
