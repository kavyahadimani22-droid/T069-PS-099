# T069-PS-099 – Freight Exchange Load Matching and Dynamic Truck Pricing Engine

A modular, placement-ready Python 3.10+ capstone application implementing an end-to-end B2B road-freight marketplace: **dynamic pricing**, **multi-constraint truck matching & driver HOS compliance**, **counter-offer bidding**, **trip lifecycle state management**, **detention/cancellation/abort handling**, **GST/RCM & TDS financial settlement**, **SQLite persistence**, **structured CSV reporting**, and a **built-in interactive Web Dashboard**—with **zero mandatory third-party dependencies**.

---

## 1. Key Capabilities (BR-01 to BR-30)

- **Dynamic Pricing (`pricing_service.py`)**
  - `max(distance, 150 km)` minimum chargeable distance (`BR-01`)
  - Demand-to-supply ratio within 200 km (`>4: +30%`, `>2.5: +20%`, `>1.5: +10%`, `<0.5: -10%`) (`BR-03`, `BR-04`)
  - Return-load density discount (`-8%` when `>=3` qualifying loads within 300 km) (`BR-05`)
  - Backhaul-poor city surcharge (`+12%`), Hazardous (`+15%`), Perishable (`+10%`, `<=6h` pickup window) (`BR-06`–`BR-08`)
  - Optional stretch goals: Multi-drop extra stop pricing (`BR-29`) & monthly fuel-index adjustment (`BR-30`)
- **Truck Eligibility, HOS & Ranking (`matching_service.py`)**
  - Weight capacity, exact or one-size-larger truck (`LCV -> 17FT -> 22FT -> 32FT_MXL -> TRAILER`), availability window, `<=150 km` pickup radius (`BR-09`–`BR-11`)
  - HAZ certification, oversize length validation, and 14-hour daily driver HOS checks with `second_driver` waiver (`BR-12`, `BR-26`)
  - Excludes carriers rated `< 3.0`, ranks by `(distance asc, rating desc, truck_id asc)`, queues top 3 offers with 30-min timeout (`BR-13`, `BR-14`, `BR-28`)
- **Counter-Bidding & Trip State Machine (`bidding_service.py`, `trip_lifecycle_service.py`)**
  - Counter-offers: `<= +5%` auto-accepted, `+5% to +15%` 60-minute shipper decision window, `> +15%` rejected (`BR-15`, `BR-16`)
  - Trip lifecycle: `MATCHED -> AT_PICKUP -> LOADED -> IN_TRANSIT -> DELIVERED -> SETTLED` plus `CANCELLED` & `ABORTED`
  - Pickup/delivery detention (`6h` free, ceiling rounding, `48h` cap at ₹300/₹500/₹800 per hr), `>48h` abort (`50%` base compensation), shipper/carrier cancel & no-show penalties, clamped carrier ratings (`1.0–5.0`) (`BR-17`–`BR-21`, `BR-27`)
- **Settlement, GST/RCM & TDS (`settlement_service.py`)**
  - Toll reimbursement capped at `lane_cap * 1.10` (`BR-22`)
  - `6%` platform fee on base freight, `5%` GST with Reverse Charge Mechanism (`RCM`) flag (`BR-23`, `BR-24`)
  - `1%` TDS on single trips `> ₹30,000` or trips crossing `₹1,00,000` annual cumulative payout (`BR-25`)
- **Persistence, Reports & Live Dashboard**
  - 3 relational SQLite DDL files (`app/database/`) + `FreightRepository`
  - 6 structured CSV reports + automated scenario validator (`validate_sample_pack_outputs.py`)
  - Zero-dependency interactive Web UI (`python run_dashboard.py`)

---

## 2. Project Structure

```text
T069-PS-099/
├── app/
│   ├── commands/
│   │   └── command_processor.py        # JSON & JSONL command dispatcher
│   ├── database/
│   │   ├── connection.py               # SQLite bootstrap & FK enforcement
│   │   ├── schema.sql                  # Master entities & lanes DDL
│   │   ├── operations_schema.sql       # Loads, trips, offers, rejections DDL
│   │   └── settlement_schema.sql       # Settlements, invoices, audit logs DDL
│   ├── models/
│   │   └── entities.py                 # Dataclasses & State enum
│   ├── repositories/
│   │   └── freight_repository.py       # SQLite persistence repository
│   ├── services/
│   │   ├── exceptions.py               # RuleError, Decimal & lane helpers
│   │   ├── pricing_service.py          # BR-01..BR-08, BR-29, BR-30
│   │   ├── matching_service.py         # BR-09..BR-13, BR-26, BR-28
│   │   ├── bidding_service.py          # BR-15..BR-16
│   │   ├── trip_lifecycle_service.py   # BR-17..BR-21, BR-27
│   │   ├── settlement_service.py       # BR-22..BR-25
│   │   ├── reporting_service.py        # Text report & 6 CSV exports
│   │   ├── sample_loader.py            # Demo & CSV sample-pack loader
│   │   └── freight_engine.py           # Core stateful orchestrator
│   └── web/
│       └── dashboard_server.py         # Interactive Web UI & JSON API
├── sample_data/                        # Multi-scenario CSV & JSONL dataset
├── examples/                           # Sample JSON & JSONL command scripts
├── outputs/                            # Generated CSVs, text report & SQLite DB
├── docs/
│   ├── diagrams/                       # ER, Class, State & Sequence diagrams
│   ├── br_test_matrix.md               # BR-01..BR-30 traceability matrix
│   ├── design_document.md / .pdf       # Architecture & rule specification
│   ├── decision_log.md                 # Engineering assumptions & decisions
│   ├── command_file_format.md          # JSON/JSONL CLI schema
│   ├── sample_data_pack.md             # Planted scenarios reference
│   ├── demo_guide.md                   # 5-minute viva / placement script
│   ├── sqlite_integration_runbook.md   # Database setup & verification guide
│   └── submission_report.md            # Capstone summary report
├── tests/                              # Modular automated unit & contract suite
├── main.py                             # Standard CLI entry point
├── run_sample_pack.py                  # Full sample-pack runner (CSV + SQLite)
├── validate_sample_pack_outputs.py     # Automated scenario output validator
├── run_commands.py                     # Standalone JSON/JSONL command runner
├── run_dashboard.py                    # Launch interactive Web Dashboard
├── run_pricing_demo.py                 # Focused pricing demo
├── run_matching_bidding_demo.py        # Focused matching & counter-bid demo
├── run_detention_settlement_demo.py    # Focused detention, GST & TDS demo
├── run_cancellation_abort_demo.py      # Focused cancel & >48h abort demo
├── run_sqlite_acceptance_demo.py       # Disposable SQLite persistence demo
├── verify_database_schema.py           # DDL schema contract verifier
├── config.py
├── pytest.ini
└── requirements.txt
```

---

## 3. Quick Start

### Step 1: Run the Full Sample Pack & Validate Outputs
```powershell
python run_sample_pack.py
python validate_sample_pack_outputs.py
```
This processes `sample_data/` and generates inside `outputs/`:
- `price_breakdowns.csv`
- `trips.csv`
- `settlements.csv`
- `shipper_invoices.csv`
- `carrier_ratings.csv`
- `rejections.csv`
- `run_report.txt`
- `freight_exchange.db` (SQLite database)

### Step 2: Launch the Interactive Web Dashboard
```powershell
python run_dashboard.py
```
Open **http://127.0.0.1:8069** in your browser to inspect live KPIs, run the dynamic pricing simulator, view truck rejection audits, and inspect GST/RCM & TDS settlements.

### Step 3: Run the Automated Test Suite
```powershell
python -m unittest discover -s tests -v
```
*(Optional, if `pytest` is installed: `python -m pytest`)*

### Step 4: Run Individual Scenario Demos or Command Files
```powershell
python main.py
python run_pricing_demo.py
python run_matching_bidding_demo.py
python run_detention_settlement_demo.py
python run_cancellation_abort_demo.py
python run_sqlite_acceptance_demo.py
python verify_database_schema.py
python run_commands.py examples/commands_full_lifecycle.jsonl --output outputs/command_results.jsonl
```

---

## 4. Documentation
- [Architecture & Design Document](docs/design_document.md)
- [BR-01 to BR-30 Test Matrix](docs/br_test_matrix.md)
- [5-Minute Demo Guide](docs/demo_guide.md)
- [Command File Format](docs/command_file_format.md)
- [Diagrams (ER, Class, State, Sequence)](docs/diagrams/er_diagram.md)
