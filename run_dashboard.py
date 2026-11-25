"""Launch the zero-dependency interactive web dashboard for T069-PS-099."""

import argparse

from app.web.dashboard_server import start_dashboard


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch T069-PS-099 Web Dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8069)
    parser.add_argument("--sample-dir", default="sample_data")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    start_dashboard(host=args.host, port=args.port, sample_dir=args.sample_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
