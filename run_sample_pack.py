"""Execute the complete T069-PS-099 sample data pack, export CSVs, and persist to SQLite."""

import argparse
from pathlib import Path

from app.commands.command_processor import run_command_file
from app.database.connection import initialize_database
from app.repositories.freight_repository import FreightRepository
from app.services.reporting_service import export_csv_reports
from app.services.sample_loader import load_engine_from_csv_dir


def run_pack(data_dir: Path, output_dir: Path, db_path: Path | None = None) -> dict:
    """Run the CSV/JSONL sample data pack end-to-end and return execution summary."""
    engine = load_engine_from_csv_dir(data_dir, post_loads=True)
    results = run_command_file(engine, data_dir / "commands.jsonl", stop_on_error=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "run_report.txt"
    report_path.write_text(engine.report() + "\n", encoding="utf-8")
    csv_files = export_csv_reports(engine, output_dir)

    target_db = db_path or (output_dir / "freight_exchange.db")
    conn = initialize_database(target_db)
    try:
        repo = FreightRepository(conn)
        repo.save_engine_snapshot(engine)
        counts = repo.fetch_summary_counts()
    finally:
        conn.close()

    return {
        "commands_executed": len(results),
        "report_path": report_path,
        "csv_files": csv_files,
        "db_path": target_db,
        "db_counts": counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run T069-PS-099 sample data pack")
    parser.add_argument("--data-dir", default="sample_data", help="Input CSV/JSONL sample directory")
    parser.add_argument("--output-dir", default="outputs", help="Output directory for CSV/text reports")
    args = parser.parse_args()

    summary = run_pack(Path(args.data_dir), Path(args.output_dir))
    print(f"Commands executed: {summary['commands_executed']}")
    print(f"Saved report: {summary['report_path']}")
    for name, path in summary["csv_files"].items():
        print(f"Saved CSV ({name}): {path}")
    print(f"Persisted SQLite DB: {summary['db_path']}")
    print(f"DB row counts: {summary['db_counts']}")


if __name__ == "__main__":
    main()
