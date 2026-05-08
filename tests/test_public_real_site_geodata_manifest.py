from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_public_real_site_geodata_manifest.py"
SPEC = importlib.util.spec_from_file_location("validate_public_real_site_geodata_manifest", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PublicRealSiteGeodataManifestTests(unittest.TestCase):
    def load_template(self) -> dict:
        return validator.read_yaml(
            ROOT / "data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml"
        )

    def test_template_manifest_is_valid(self) -> None:
        validator.validate_manifest(self.load_template())

    def test_requires_swissalti3d(self) -> None:
        manifest = self.load_template()
        manifest["required_datasets"] = []

        with self.assertRaisesRegex(validator.ManifestError, "swisstopo_swissalti3d"):
            validator.validate_manifest(manifest)

    def test_rejects_non_lv95_crs(self) -> None:
        manifest = self.load_template()
        manifest["selected_domain"]["coordinate_reference_system"]["epsg"] = 4326

        with self.assertRaisesRegex(validator.ManifestError, "EPSG:2056"):
            validator.validate_manifest(manifest)

    def test_prepared_manifest_requires_tiles_and_outputs(self) -> None:
        manifest = self.load_template()
        manifest["pilot_status"] = "prepared_private_local"
        manifest["selected_domain"]["extent_lv95_m"] = {
            "xmin": 2600000.0,
            "ymin": 1200000.0,
            "xmax": 2601000.0,
            "ymax": 1201000.0,
        }

        with self.assertRaisesRegex(validator.ManifestError, "source_tiles"):
            validator.validate_manifest(manifest)

    def test_rejects_missing_claim_boundary(self) -> None:
        manifest = copy.deepcopy(self.load_template())
        manifest["claim_boundary"]["unsupported_current_claims"].remove("risk_map")

        with self.assertRaisesRegex(validator.ManifestError, "risk_map"):
            validator.validate_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
