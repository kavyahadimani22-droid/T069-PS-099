"""JSON command-file reader. The built-in demonstration uses Python objects instead of external data files."""
import json
from pathlib import Path

def load_command_file(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Command file must contain a JSON array of command objects")
    return data
