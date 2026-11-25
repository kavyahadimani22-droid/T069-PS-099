import tempfile
import unittest
from pathlib import Path

from app.commands.command_processor import run_command_file
from app.database.connection import initialize_database
from app.repositories.freight_repository import FreightRepository
from app.services.sample_loader import load_engine_from_csv_dir


class SqliteRepositoryTests(unittest.TestCase):
    def test_snapshot_roundtrip_persists_all_entities(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = load_engine_from_csv_dir("sample_data", post_loads=True)
            run_command_file(engine, "sample_data/commands.jsonl", stop_on_error=True)

            conn = initialize_database(db_path)
            try:
                repo = FreightRepository(conn)
                repo.save_engine_snapshot(engine)
                counts = repo.fetch_summary_counts()
                self.assertEqual(counts["shippers"], 4)
                self.assertEqual(counts["carriers"], 5)
                self.assertEqual(counts["trucks"], 11)
                self.assertEqual(counts["loads"], 11)
                self.assertEqual(counts["trips"], 11)
                self.assertEqual(counts["settlements"], 5)
                self.assertEqual(counts["shipper_invoices"], 5)
                self.assertGreater(counts["audit_logs"], 10)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
