"""Disposable SQLite acceptance demo verifying schema bootstrap and persistence."""

import tempfile
from pathlib import Path

from app.commands.command_processor import run_command_file
from app.database.connection import initialize_database
from app.repositories.freight_repository import FreightRepository
from app.services.sample_loader import load_engine_from_csv_dir


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "freight_acceptance_test.db"
        engine = load_engine_from_csv_dir("sample_data", post_loads=True)
        run_command_file(engine, "sample_data/commands.jsonl", stop_on_error=True)

        conn = initialize_database(db_path)
        try:
            repo = FreightRepository(conn)
            repo.save_engine_snapshot(engine)
            counts = repo.fetch_summary_counts()
            print(f"SQLite acceptance DB created at: {db_path}")
            for table, count in counts.items():
                print(f"  {table}: {count} rows")
        finally:
            conn.close()


if __name__ == "__main__":
    main()
