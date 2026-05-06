import tempfile
import unittest
from pathlib import Path

from scripts import audit_local_artifacts as audit


class ArtifactAuditTest(unittest.TestCase):
    def test_summarize_targets_counts_files_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_root = root / "validation" / "results"
            artifact_root.mkdir(parents=True)
            (artifact_root / "a.txt").write_text("abc")
            (artifact_root / "nested").mkdir()
            (artifact_root / "nested" / "b.txt").write_text("de")

            summaries = audit.summarize_targets([Path("validation/results")], root=root)

            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].path, "validation/results")
            self.assertTrue(summaries[0].exists)
            self.assertEqual(summaries[0].file_count, 2)
            self.assertEqual(summaries[0].total_bytes, 5)

    def test_threshold_failure_is_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_root = root / "hazard" / "results"
            artifact_root.mkdir(parents=True)
            (artifact_root / "grid.asc").write_text("1234")

            summaries = audit.summarize_targets([Path("hazard/results")], root=root)
            stale = audit.stale_candidates(summaries, stale_min_bytes=4)

            self.assertEqual([summary.path for summary in stale], ["hazard/results"])


if __name__ == "__main__":
    unittest.main()
