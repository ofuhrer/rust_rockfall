from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib import workflow_validation as helpers


class WorkflowValidationHelperTests(unittest.TestCase):
    class HelperError(ValueError):
        pass

    def test_read_yaml_requires_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.yaml"
            path.write_text(yaml.safe_dump({"name": "ok"}, sort_keys=False), encoding="utf-8")

            data = helpers.read_yaml(path, self.HelperError)

            self.assertEqual(data["name"], "ok")

    def test_read_yaml_rejects_non_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.yaml"
            path.write_text("- a\n- b\n", encoding="utf-8")

            with self.assertRaisesRegex(self.HelperError, "must be an object"):
                helpers.read_yaml(path, self.HelperError)

    def test_resolve_repo_path_and_normalize_text(self) -> None:
        root = Path("/tmp/workflow-validation-root")

        self.assertEqual(helpers.resolve_repo_path(root, "nested/file.yaml"), root / "nested/file.yaml")
        self.assertEqual(helpers.resolve_repo_path(root, Path("/abs/file.yaml")), Path("/abs/file.yaml"))
        self.assertEqual(helpers.normalize_text("  folder\\sub\x00file  "), "folder/subfile")

    def test_sha256_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.txt"
            path.write_text("abc", encoding="utf-8")

            self.assertEqual(
                helpers.sha256_file(path),
                hashlib.sha256(b"abc").hexdigest(),
            )
            helpers.require_sha256_hex("a" * 64, "checksum", self.HelperError)

            with self.assertRaisesRegex(self.HelperError, "SHA-256"):
                helpers.require_sha256_hex("not-a-digest", "checksum", self.HelperError)

    def test_required_path_and_checksum_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "input.yaml"
            path.write_text("schema: v1\n", encoding="utf-8")
            resolved = helpers.require_paths_exist(
                {"input": "input.yaml"},
                self.HelperError,
                root=root,
                label_prefix="record",
            )
            self.assertEqual(resolved["input"], path)

            checksums = helpers.require_checksum_fields(
                {
                    "required_sha": "a" * 64,
                    "optional_sha": None,
                },
                ("required_sha", "optional_sha"),
                self.HelperError,
                label_prefix="artifact_checksums",
                allow_none=True,
            )
            self.assertEqual(checksums["required_sha"], "a" * 64)
            self.assertIsNone(checksums["optional_sha"])

            with self.assertRaisesRegex(self.HelperError, "record\\.missing"):
                helpers.require_paths_exist({"missing": "missing.txt"}, self.HelperError, root=root, label_prefix="record")

            with self.assertRaisesRegex(self.HelperError, "artifact_checksums\\.required_sha"):
                helpers.require_checksum_fields(
                    {"required_sha": "invalid"},
                    ("required_sha",),
                    self.HelperError,
                )

    def test_blocked_report_helper(self) -> None:
        report = helpers.build_blocked_report(
            schema_version="example_v1",
            status_key="example_status",
            missing_inputs=["", "b", "a", "a"],
            blocked_reason="missing inputs",
            extra_fields={"notes": []},
        )

        self.assertEqual(report["schema_version"], "example_v1")
        self.assertEqual(report["example_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["a", "b"])
        self.assertEqual(report["blocked_reason"], "missing inputs")
        self.assertEqual(report["notes"], [])

    def test_claim_boundary_and_text_scan_helpers(self) -> None:
        helpers.require_false_fields(
            {
                "annual_frequency_supported": False,
                "physical_probability_supported": False,
                "return_period_supported": False,
                "operational_hazard_map_supported": False,
                "risk_or_exposure_supported": False,
            },
            helpers.DEFAULT_CLAIM_BOUNDARY_FIELDS,
            self.HelperError,
        )

        with self.assertRaisesRegex(self.HelperError, "claim_boundary\\.annual_frequency_supported"):
            helpers.require_false_fields(
                {
                    "annual_frequency_supported": True,
                    "physical_probability_supported": False,
                    "return_period_supported": False,
                    "operational_hazard_map_supported": False,
                    "risk_or_exposure_supported": False,
                },
                helpers.DEFAULT_CLAIM_BOUNDARY_FIELDS,
                self.HelperError,
            )

        helpers.scan_text_for_misleading_claims(
            {
                "claim_boundary": {"annual_frequency_supported": False},
                "notes": ["unsupported future product boundary"],
                "context": {"summary": "out of scope"},
            },
            require_fn=lambda condition, message: helpers.require(condition, message, self.HelperError),
            patterns=helpers.DEFAULT_MISLEADING_PATTERNS,
            skip_keys={"claim_boundary"},
        )

        with self.assertRaisesRegex(self.HelperError, "misleading current-product claim"):
            helpers.scan_text_for_misleading_claims(
                {"notes": ["This is a risk map."]},
                require_fn=lambda condition, message: helpers.require(condition, message, self.HelperError),
                patterns=helpers.DEFAULT_MISLEADING_PATTERNS,
            )

    def test_render_status_message(self) -> None:
        message = helpers.render_status_message(
            "sample record",
            Path("record.yaml"),
            {"record_status": "candidate_not_authorized", "count": 3},
            "record_status",
            extra_fields=(("count", "item_count"),),
        )

        self.assertEqual(
            message,
            "sample record is valid: record.yaml (candidate_not_authorized, item_count=3)",
        )


if __name__ == "__main__":
    unittest.main()
