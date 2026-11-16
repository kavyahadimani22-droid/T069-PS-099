"""Freight Exchange Load Matching and Dynamic Truck Pricing Engine."""
from src.engine import FreightEngine
from src.sample_data import build_sample_engine
from src.file_handler import load_command_file
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Freight Exchange command-line engine")
    parser.add_argument("--commands", help="Optional JSON command file. If omitted, built-in Python sample data is used.")
    parser.add_argument("--output", default="outputs/run_report.txt", help="Report output path")
    parser.add_argument("--demo", action="store_true", help="Run the built-in end-to-end demonstration")
    args = parser.parse_args()

    engine = build_sample_engine()
    if args.commands:
        commands = load_command_file(args.commands)
        engine.execute_commands(commands)
    else:
        engine.run_demo()

    report = engine.render_report()
    print(report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report + "\n", encoding="utf-8")
    print(f"\nReport written to: {output}")

if __name__ == "__main__":
    main()
