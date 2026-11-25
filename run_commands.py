"""Execute a JSON or JSONL command file and emit structured JSONL results."""

import argparse
import json
from pathlib import Path

from app.commands.command_processor import run_command_file
from app.services.sample_loader import create_engine, load_engine_from_csv_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JSON/JSONL commands against FreightEngine")
    parser.add_argument("command_file", help="Path to .json or .jsonl command file")
    parser.add_argument("--output", default="outputs/command_results.jsonl", help="Output JSONL path")
    parser.add_argument("--sample-dir", help="Optional CSV directory to pre-load master data")
    args = parser.parse_args()

    engine = load_engine_from_csv_dir(args.sample_dir, post_loads=False) if args.sample_dir else create_engine()
    results = run_command_file(engine, args.command_file, stop_on_error=False)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")
    print(f"Processed {len(results)} commands -> {out_path}")


if __name__ == "__main__":
    main()
