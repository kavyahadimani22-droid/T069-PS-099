# T069-PS-099 – Freight Exchange Load Matching and Dynamic Truck Pricing Engine

A Python 3.10+ command-line implementation of a freight marketplace matching and pricing engine. No UI and no third-party dependencies are required. Demonstration data is embedded in Python.

## Requirements
- Python 3.10 or later
- Standard library only

## Run
```bash
python main.py
```
This runs the built-in sample scenario, prints the report and writes `outputs/run_report.txt`.

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Optional command file
The command file is a JSON array. Master data and sample loads remain in Python. Example:
```json
[
  {"op": "MATCH"},
  {"op": "ADVANCE", "minutes": 30},
  {"op": "COUNTER", "trip_id": "TRIP-LD-001", "amount": 9000, "elapsed_minutes": 15},
  {"op": "EVENT", "trip_id": "TRIP-LD-001", "event": "AT_PICKUP"},
  {"op": "EVENT", "trip_id": "TRIP-LD-001", "event": "LOADED"},
  {"op": "EVENT", "trip_id": "TRIP-LD-001", "event": "IN_TRANSIT"},
  {"op": "EVENT", "trip_id": "TRIP-LD-001", "event": "DELIVERED", "data": {"late_hours": 0}},
  {"op": "EVENT", "trip_id": "TRIP-LD-001", "event": "SETTLE", "data": {"toll_actual": 500, "pickup_detention_hours": 7, "delivery_detention_hours": 6}}
]
```

## Folder structure
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
│   ├── file_handler.py
│   ├── sample_data.py
│   ├── pricing.py
│   ├── matching.py
│   ├── bidding.py
│   ├── trip_manager.py
│   ├── settlement.py
│   ├── rating.py
│   ├── validation.py
│   └── engine.py
├── tests/
│   └── test_business_rules.py
├── docs/
│   ├── design_document.md
│   └── decision_log.md
└── outputs/
```

## Implementation notes
- Prices are calculated with `Decimal` and rounded to whole rupees using half-up rounding.
- The distance table is embedded in `src/sample_data.py`; reverse lane lookup is supported.
- Rates and rule constants are centralized in `config.py`.
- The implementation assumptions and limitations are listed in `docs/design_document.md`.
- All business rules BR-01 through BR-30 are registered in the design document. BR-29 and BR-30 are optional stretch goals.

## Important scope note
The supplied problem statement refers to sample data, expected output files and toll files that are not attached here. This repository includes an internally consistent demo dataset, not the organizer's private evaluation dataset. Exact hidden-evaluation parity requires their actual input schema and clarifications for the assumptions documented in the design document.
