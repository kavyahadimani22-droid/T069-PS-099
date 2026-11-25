import tempfile
import unittest
from pathlib import Path

from run_sample_pack import run_pack
from validate_sample_pack_outputs import validate_outputs


class SamplePackAndValidationTests(unittest.TestCase):
    def test_full_sample_pack_and_validator_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            summary = run_pack(Path("sample_data"), out_dir)
            self.assertGreaterEqual(summary["commands_executed"], 35)
            checks = validate_outputs(out_dir)
            failed = [(name, detail) for name, ok, detail in checks if not ok]
            self.assertEqual(failed, [], f"Failed checks: {failed}")


if __name__ == "__main__":
    unittest.main()
