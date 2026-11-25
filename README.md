# T069-PS-099 – Freight Exchange Load Matching and Dynamic Truck Pricing Engine

Python 3.10+ command-line application. All demonstration master data, city distances, sample load and toll caps are stored in Python (`src/sample_data.py`). No UI and no third-party packages.

## Run
```bash
python main.py
```
Report prints to terminal and saves to `outputs/run_report.txt`.

## Tests
```bash
python -m unittest discover -s tests -v
```

## Optional JSON command file
```bash
python main.py --commands commands.json
```
Example:
```json
[
  {"op":"MATCH"},
  {"op":"ACCEPT","load_id":"LD-001"},
  {"op":"EVENT","trip_id":"TRIP-LD-001","event":"AT_PICKUP"},
  {"op":"EVENT","trip_id":"TRIP-LD-001","event":"LOADED"},
  {"op":"EVENT","trip_id":"TRIP-LD-001","event":"IN_TRANSIT"},
  {"op":"EVENT","trip_id":"TRIP-LD-001","event":"DELIVERED","data":{"late_hours":0}},
  {"op":"EVENT","trip_id":"TRIP-LD-001","event":"SETTLE","data":{"toll_actual":500,"pickup_detention_hours":7,"delivery_detention_hours":6}}
]
```
Other operations: `ADVANCE`, `DECLINE`, `COUNTER`, `SHIPPER_DECISION`, `CANCEL_SHIPPER`, `CANCEL_CARRIER`, `NO_SHOW`, `ABORT`.

## Project structure
```text
T069-PS-099/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── rules.py
│   ├── engine.py
│   ├── sample_data.py
│   └── file_handler.py
├── tests/
│   └── test_all_rules.py
├── docs/
│   ├── design_document.md
│   ├── design_document.pdf
│   └── decision_log.md
└── outputs/
```

## Notes and assumptions
- Money uses `Decimal` and whole-rupee half-up rounding.
- Percentage adjustments (surge, return load, backhaul-poor and material) are additive on base freight before one rounding.
- Surge thresholds are strict `>`; low-demand is strict `<0.5`.
- A truck can be exact requested type or one size larger; rate remains requested type's rate.
- Pickup/delivery detention is independently charged after six free hours; each interval rounds up and caps at 48 chargeable hours.
- TDS uses strict “above” tests and the annual threshold crossing trip triggers TDS.
- The supplied assignment does not define the source format for event timestamps, carrier rating history, toll-file schema or exact expected output serialization. These are documented assumptions, not claimed as organizer-provided schemas.
- This demo dataset is illustrative and is not the organizer's 30-truck/90-load evaluation data.
