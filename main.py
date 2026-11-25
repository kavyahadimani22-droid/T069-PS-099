"""Command-line entry point for the T069-PS-099 Freight Exchange Engine."""

import argparse
from pathlib import Path

from app.commands.command_processor import run_command_file
from app.services.reporting_service import export_csv_reports
from app.services.sample_loader import create_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="T069-PS-099 Freight Exchange Engine")
    parser.add_argument("--commands", help="Optional JSON or JSONL command file")
    parser.add_argument("--output", default="outputs/run_report.txt", help="Output text report path")
    parser.add_argument("--export-csv-dir", help="Optional directory to write structured CSV reports")
    args = parser.parse_args()

    engine = create_engine()
    if args.commands:
        run_command_file(engine, args.commands, stop_on_error=True)
    else:
        engine.run_demo()

    report = engine.report()
    print(report)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\nSaved report: {out}")

    if args.export_csv_dir:
        csv_paths = export_csv_reports(engine, args.export_csv_dir)
        for name, path in csv_paths.items():
            print(f"Saved CSV ({name}): {path}")


if __name__ == "__main__":
    main()
