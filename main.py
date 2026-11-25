import argparse
from pathlib import Path
from src.sample_data import create_engine
from src.file_handler import run_command_file

def main():
    parser = argparse.ArgumentParser(description="T069-PS-099 Freight Exchange Engine")
    parser.add_argument("--commands", help="Optional JSON command file")
    parser.add_argument("--output", default="outputs/run_report.txt")
    args = parser.parse_args()
    engine = create_engine()
    if args.commands:
        run_command_file(engine, args.commands)
    else:
        engine.run_demo()
    report = engine.report()
    print(report)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\nSaved report: {out}")

if __name__ == "__main__":
    main()
