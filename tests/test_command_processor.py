import tempfile
import unittest
from pathlib import Path

from app.commands.command_processor import run_command_file, run_commands
from app.models import State
from app.services.sample_loader import create_engine


class CommandProcessorTests(unittest.TestCase):
    def test_json_command_file_execution(self):
        engine = create_engine()
        results = run_command_file(engine, Path("examples/commands_basic.json"), stop_on_error=True)
        self.assertEqual(len(results), 7)
        self.assertEqual(engine.trips["TRIP-LD-001"].state, State.SETTLED)

    def test_jsonl_full_lifecycle_execution(self):
        engine = create_engine()
        results = run_command_file(engine, Path("examples/commands_full_lifecycle.jsonl"), stop_on_error=True)
        self.assertEqual(len(results), 12)
        self.assertEqual(engine.trips["TRIP-LD-DEMO"].state, State.SETTLED)

    def test_error_isolation_continues_by_default(self):
        engine = create_engine()
        cmds = [
            {"op": "UNKNOWN_OP"},
            {"op": "MATCH"},
            {"op": "ACCEPT", "load_id": "LD-001"},
        ]
        results = run_commands(engine, cmds, stop_on_error=False)
        self.assertEqual(results[0]["status"], "ERROR")
        self.assertEqual(results[1]["status"], "OK")
        self.assertEqual(results[2]["status"], "ACCEPTED")

    def test_empty_file_returns_empty_list(self):
        engine = create_engine()
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "empty.jsonl"
            p.write_text("", encoding="utf-8")
            self.assertEqual(run_command_file(engine, p), [])


if __name__ == "__main__":
    unittest.main()
