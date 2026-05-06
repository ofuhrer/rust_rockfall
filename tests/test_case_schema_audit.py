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


if __name__ == "__main__":
    unittest.main()
